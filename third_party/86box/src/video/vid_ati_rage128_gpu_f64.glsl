/*
 * 86Box    A hypervisor and IBM PC system emulator that specializes in
 *          running old operating systems and software designed for IBM
 *          PC systems and compatibles from 1981 through fairly recent
 *          system designs based on the PCI bus.
 *
 *          This file is part of the 86Box distribution.
 *
 *          ATI Rage 128 Pro -- GPU backend, software IEEE-754 binary64.
 *
 *          The interpreter steps depth across a span in C doubles, and
 *          the GPU backend must reproduce every bit of that chain. Apple
 *          GPUs have no 64-bit float type, so the kernels that need the
 *          chain (vid_ati_rage128_gpu_seg.comp and the z-ladder pre-pass
 *          vid_ati_rage128_gpu_lad.comp) include this file and run the
 *          arithmetic on 64-bit words instead: add, multiply, compares,
 *          truncation to a 32-bit integer and the depth quantize, all
 *          with round-to-nearest-even.
 *
 *          f64_add takes every class of operand: zeros of both signs,
 *          subnormals, infinities and NaN, with the IEEE results (a NaN
 *          result is one quiet NaN pattern, not the operand's payload).
 *          f64_mul takes finite normal or zero inputs only and does not
 *          propagate infinity or NaN, so a caller that can see a NaN
 *          gates on f64_is_nan before it; the quantizer clamps NaN to 0
 *          itself, matching the interpreter's inverted compare.
 *
 *          KairoX86#326: the 64-bit words are uvec2 (x the low 32 bits,
 *          y the high), with the integer operations written in 32-bit
 *          ones (u64_*, i64_*), so the kernels need no shaderInt64 and
 *          run on GPUs without it (the RP6's). Every operation gives the
 *          bits the 64-bit one gives.
 *
 * Authors: skiretic.
 *
 *          Copyright 2026 skiretic.
 */

/* ---- 64-bit integers on uvec2 (KairoX86#326) ---- */

uvec2 u64(uint lo, uint hi) { return uvec2(lo, hi); }
const uvec2 U64_0 = uvec2(0u, 0u);
const uvec2 U64_1 = uvec2(1u, 0u);

uvec2 u64_add(uvec2 a, uvec2 b)
{
    uint c;
    uint lo = uaddCarry(a.x, b.x, c);
    return uvec2(lo, a.y + b.y + c);
}

uvec2 u64_sub(uvec2 a, uvec2 b)
{
    uint br;
    uint lo = usubBorrow(a.x, b.x, br);
    return uvec2(lo, a.y - b.y - br);
}

/* shifts by n, any n >= 0 (64 and up give 0, as the C shift of a value
   that is then masked would not, so callers keep n below 64 where the
   64-bit code did) */
uvec2 u64_shl(uvec2 a, int n)
{
    if (n <= 0)
        return a;
    if (n >= 64)
        return U64_0;
    if (n >= 32)
        return uvec2(0u, a.x << uint(n - 32));
    return uvec2(a.x << uint(n), (a.y << uint(n)) | (a.x >> uint(32 - n)));
}

uvec2 u64_shr(uvec2 a, int n)
{
    if (n <= 0)
        return a;
    if (n >= 64)
        return U64_0;
    if (n >= 32)
        return uvec2(a.y >> uint(n - 32), 0u);
    return uvec2((a.x >> uint(n)) | (a.y << uint(32 - n)), a.y >> uint(n));
}

uvec2 u64_and(uvec2 a, uvec2 b) { return a & b; }
uvec2 u64_or(uvec2 a, uvec2 b) { return a | b; }
bool  u64_eq(uvec2 a, uvec2 b) { return a.x == b.x && a.y == b.y; }
bool  u64_is0(uvec2 a) { return (a.x | a.y) == 0u; }
bool  u64_lt(uvec2 a, uvec2 b) { return a.y < b.y || (a.y == b.y && a.x < b.x); }
bool  u64_gt(uvec2 a, uvec2 b) { return u64_lt(b, a); }
bool  u64_ge(uvec2 a, uvec2 b) { return !u64_lt(a, b); }

/* the low 64 bits of a * b */
uvec2 u64_mul(uvec2 a, uvec2 b)
{
    uint hi, lo;
    umulExtended(a.x, b.x, hi, lo);
    return uvec2(lo, hi + a.x * b.y + a.y * b.x);
}

/* a / b and a % b, b nonzero (restoring division, bit by bit) */
void u64_divmod(uvec2 a, uvec2 b, out uvec2 q, out uvec2 r)
{
    q = U64_0;
    r = U64_0;
    for (int i = 63; i >= 0; i--) {
        r = u64_shl(r, 1);
        r.x |= (i >= 32) ? ((a.y >> uint(i - 32)) & 1u) : ((a.x >> uint(i)) & 1u);
        if (u64_ge(r, b)) {
            r = u64_sub(r, b);
            if (i >= 32)
                q.y |= 1u << uint(i - 32);
            else
                q.x |= 1u << uint(i);
        }
    }
}

/* two's complement signed values in the same words */
uvec2 i64_from_int(int v) { return uvec2(uint(v), (v < 0) ? 0xffffffffu : 0u); }
uvec2 i64_neg(uvec2 a) { return u64_sub(U64_0, a); }
bool  i64_is_neg(uvec2 a) { return (a.y >> 31) != 0u; }
bool  i64_gt0(uvec2 a) { return !i64_is_neg(a) && !u64_is0(a); }

/* float(v) of a signed 64-bit value, rounded to nearest, ties to even, as
   the 64-bit conversion rounds */
float i64_to_float(uvec2 v)
{
    bool  neg = i64_is_neg(v);
    uvec2 m   = neg ? i64_neg(v) : v;

    if (u64_is0(m))
        return 0.0;
    int top = (m.y != 0u) ? (32 + findMSB(m.y)) : findMSB(m.x);
    int sh  = top - 23; /* the bits below the top 24 */
    float f;

    if (sh <= 0)
        f = float(m.x); /* below 2^24: exact */
    else {
        uvec2 kept = u64_shr(m, sh);
        uvec2 rest = u64_sub(m, u64_shl(kept, sh));
        uvec2 hlf  = u64_shl(U64_1, sh - 1);
        uint  mant = kept.x;
        if (u64_gt(rest, hlf) || (u64_eq(rest, hlf) && (mant & 1u) != 0u))
            mant++; /* to nearest, ties to even (a carry to 2^24 stays exact) */
        f = ldexp(float(mant), sh);
    }
    return neg ? -f : f;
}

/* ---- binary64 on those words ---- */

const uvec2 F64_SIGN  = uvec2(0x00000000u, 0x80000000u);
const uvec2 F64_MAG   = uvec2(0xffffffffu, 0x7fffffffu); /* ~F64_SIGN */
const uvec2 F64_MANT  = uvec2(0xffffffffu, 0x000fffffu);
const uvec2 F64_HID   = uvec2(0x00000000u, 0x00100000u);
const uvec2 F64_INF   = uvec2(0x00000000u, 0x7ff00000u); /* magnitude of an infinity */
const uvec2 F64_QNAN  = uvec2(0x00000000u, 0x7ff80000u); /* the quiet NaN f64_add returns */

const uvec2 F64_ZERO   = uvec2(0x00000000u, 0x00000000u);
const uvec2 F64_HALF   = uvec2(0x00000000u, 0x3fe00000u); /* 0.5 */
const uvec2 F64_ONE    = uvec2(0x00000000u, 0x3ff00000u); /* 1.0 */
const uvec2 F64_65535  = uvec2(0x00000000u, 0x40efffe0u); /* 65535.0    */
const uvec2 F64_ZMAX24 = uvec2(0xe0000000u, 0x416fffffu); /* 16777215.0 */
const uvec2 F64_255    = uvec2(0x00000000u, 0x406fe000u); /* 255.0 (fog table quant) */

/* the exponent field and the sign bit of a word */
int  f64_exp(uvec2 a) { return int((a.y >> 20) & 0x7ffu); }
uint f64_sgn(uvec2 a) { return a.y >> 31; }

uvec2
f64_add(uvec2 a, uvec2 b)
{
    uvec2 amag = a & F64_MAG;
    uvec2 bmag = b & F64_MAG;

    /* NaN and infinity first: a NaN operand gives NaN, so do two
       infinities of opposite sign; otherwise an infinite operand is the
       sum, whatever the other operand. */
    if (u64_gt(amag, F64_INF) || u64_gt(bmag, F64_INF))
        return F64_QNAN;
    if (u64_eq(amag, F64_INF))
        return (u64_eq(bmag, F64_INF) && !u64_eq(a, b)) ? F64_QNAN : a;
    if (u64_eq(bmag, F64_INF))
        return b;
    if (u64_is0(amag))
        return u64_is0(bmag) ? (a & b) : b; /* +0 unless both -0 */
    if (u64_is0(bmag))
        return a;
    if (u64_lt(amag, bmag)) {
        uvec2 t = a; a = b; b = t;
        t = amag; amag = bmag; bmag = t;
    }
    int ea = f64_exp(amag);
    int eb = f64_exp(bmag);
    /* A subnormal has exponent field 0 and no implicit bit, and its
       significand is spaced like exponent 1, so it aligns and rounds as
       an exponent-1 value. */
    uvec2 ma = u64_shl((amag & F64_MANT) | ((ea != 0) ? F64_HID : U64_0), 3); /* GRS tail */
    uvec2 mb = u64_shl((bmag & F64_MANT) | ((eb != 0) ? F64_HID : U64_0), 3);
    uint  sa = f64_sgn(a);
    uint  sb = f64_sgn(b);
    uvec2 mbs;

    ea = max(ea, 1);
    eb = max(eb, 1);
    int sh = ea - eb;

    if (sh >= 56)
        mbs = U64_1; /* pure sticky (bmag nonzero) */
    else if (sh > 0) {
        uvec2 rem = mb & u64_sub(u64_shl(U64_1, sh), U64_1);
        mbs = u64_shr(mb, sh) | (u64_is0(rem) ? U64_0 : U64_1);
    } else
        mbs = mb;

    uvec2 mr;
    int   er = ea;

    if (sa == sb)
        mr = u64_add(ma, mbs);
    else {
        mr = u64_sub(ma, mbs);
        if (u64_is0(mr))
            return F64_ZERO; /* exact cancel -> +0 in RNE */
    }
    if (u64_ge(mr, u64_shl(U64_1, 56))) {
        mr = u64_shr(mr, 1) | (mr & U64_1); /* keep sticky */
        er++;
    } else {
        /* normalize no further than exponent 1: below it the result is
           a subnormal, kept at exponent 1's spacing */
        while (u64_lt(mr, u64_shl(U64_1, 55)) && er > 1) {
            mr = u64_shl(mr, 1);
            er--;
        }
    }
    /* round-to-nearest-even on the 3 GRS bits */
    uint  grs  = mr.x & 7u;
    uvec2 keep = u64_shr(mr, 3);

    if (grs > 4u || (grs == 4u && (keep.x & 1u) != 0u))
        keep = u64_add(keep, U64_1);
    if (u64_ge(keep, u64_shl(U64_1, 53))) {
        keep = u64_shr(keep, 1);
        er++;
    }
    if (er >= 2047)
        return uvec2(0u, sa << 31) | F64_INF; /* overflow */
    if (er == 1 && u64_lt(keep, F64_HID))
        er = 0; /* subnormal: no implicit bit, exponent field 0 */
    return uvec2(0u, (sa << 31) | (uint(er) << 20)) | (keep & F64_MANT);
}

uvec2
f64_mul(uvec2 a, uvec2 b)
{
    uint  sr   = f64_sgn(a) ^ f64_sgn(b);
    uvec2 amag = a & F64_MAG;
    uvec2 bmag = b & F64_MAG;

    if (u64_is0(amag) || u64_is0(bmag))
        return uvec2(0u, sr << 31);

    int   ea = f64_exp(amag);
    int   eb = f64_exp(bmag);
    uvec2 ma = (amag & F64_MANT) | F64_HID;
    uvec2 mb = (bmag & F64_MANT) | F64_HID;

    /* 53x53 -> 106-bit product via 32-bit limbs */
    uvec2 p00, p01, p10, p11;
    umulExtended(ma.x, mb.x, p00.y, p00.x);
    umulExtended(ma.x, mb.y, p01.y, p01.x);
    umulExtended(ma.y, mb.x, p10.y, p10.x);
    umulExtended(ma.y, mb.y, p11.y, p11.x);
    uvec2 mid = u64_add(p01, p10);
    uvec2 lo  = u64_add(p00, u64_shl(mid, 32));
    uvec2 hi  = u64_add(u64_add(p11, u64_shr(mid, 32)),
                        u64_add(u64_lt(mid, p01) ? uvec2(0u, 1u) : U64_0,
                                u64_lt(lo, p00) ? U64_1 : U64_0));

    /* product in [2^104, 2^106); top bit at 105 -> mant in [2,4) */
    int   top105 = u64_ge(hi, u64_shl(U64_1, 41)) ? 1 : 0;
    int   sh     = 52 + top105;
    uvec2 keep   = u64_shl(hi, 64 - sh) | u64_shr(lo, sh);
    uvec2 rnd    = u64_shr(lo, sh - 1) & U64_1;
    uvec2 stk    = lo & u64_sub(u64_shl(U64_1, sh - 1), U64_1);
    int   er     = ea + eb - 1023 + top105;

    if (!u64_is0(rnd) && (!u64_is0(stk) || (keep.x & 1u) != 0u))
        keep = u64_add(keep, U64_1);
    if (u64_ge(keep, u64_shl(U64_1, 53))) {
        keep = u64_shr(keep, 1);
        er++;
    }
    return uvec2(0u, (sr << 31) | (uint(er) << 20)) | (keep & F64_MANT);
}

/* quiet or signaling NaN */
bool
f64_is_nan(uvec2 a)
{
    return u64_gt(a & F64_MAG, F64_INF);
}

/* a > 0.0 ? (finite a) */
bool
f64_gt_zero(uvec2 a)
{
    return f64_sgn(a) == 0u && !u64_is0(a & F64_MAG);
}

/* a > b for b a positive constant, a finite */
bool
f64_gt_pos(uvec2 a, uvec2 b)
{
    if (f64_sgn(a) != 0u)
        return false;
    return u64_gt(a, b);
}

/* (uint32_t) of a non-negative double < 2^32 (C trunc toward zero) */
uint
f64_to_u32(uvec2 a)
{
    if (f64_sgn(a) != 0u || u64_is0(a & F64_MAG))
        return 0u;
    int e = f64_exp(a) - 1023;

    if (e < 0)
        return 0u;
    uvec2 m = (a & F64_MANT) | F64_HID;

    if (e <= 52)
        return u64_shr(m, 52 - e).x;
    return u64_shl(m, e - 52).x;
}

/* the interpreter's z quantize chain on a raw zline value:
   clamp [0,1], * zmax + 0.5, clamp to zmax, trunc. zmaxd is zmax as a
   double; the clamp to 1.0 first is what keeps z*zmax+0.5 exact, so a
   far/sky fragment lands on exactly zmax instead of one ULP past it. */
uint
f64_zq(uvec2 zc, uvec2 zmaxd)
{
    /* NaN passes the raw sign+magnitude gt tests; the oracle's inverted
       compare (!(zc > 0.0)) sends it to 0 before the fog index or the
       quantize can see it */
    if (f64_is_nan(zc) || !f64_gt_zero(zc))
        zc = F64_ZERO;
    if (f64_gt_pos(zc, F64_ONE))
        zc = F64_ONE;
    uvec2 zq = f64_add(f64_mul(zc, zmaxd), F64_HALF);

    if (f64_gt_pos(zq, zmaxd))
        zq = zmaxd;
    return f64_to_u32(zq);
}

uint
f64_zq16(uvec2 zc)
{
    return f64_zq(zc, F64_65535);
}
