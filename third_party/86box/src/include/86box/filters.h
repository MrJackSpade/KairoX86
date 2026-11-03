#ifndef EMU_FILTERS_H
#define EMU_FILTERS_H

#define NCoef 2

/* fc=150Hz */
static inline float
adgold_highpass_iir(int i, float NewSample)
{
    float ACoef[NCoef + 1] = {
        0.98657437157334349000,
        -1.97314874314668700000,
        0.98657437157334349000
    };

    float BCoef[NCoef + 1] = {
        1.00000000000000000000,
        -1.97223372919758360000,
        0.97261396931534050000
    };

    static float y[2][NCoef + 1]; /* output samples */
    static float x[2][NCoef + 1]; /* input samples */
    int          n;

    /* shift the old samples */
    for (n = NCoef; n > 0; n--) {
        x[i][n] = x[i][n - 1];
        y[i][n] = y[i][n - 1];
    }

    /* Calculate the new output */
    x[i][0] = NewSample;
    y[i][0] = ACoef[0] * x[i][0];
    for (n = 1; n <= NCoef; n++)
        y[i][0] += ACoef[n] * x[i][n] - BCoef[n] * y[i][n];

    return y[i][0];
}

/* fc=150Hz */
static inline float
adgold_lowpass_iir(int i, float NewSample)
{
    float ACoef[NCoef + 1] = {
        0.00009159473951071446,
        0.00018318947902142891,
        0.00009159473951071446
    };

    float BCoef[NCoef + 1] = {
        1.00000000000000000000,
        -1.97223372919526560000,
        0.97261396931306277000
    };

    static float y[2][NCoef + 1]; /* output samples */
    static float x[2][NCoef + 1]; /* input samples */
    int          n;

    /* shift the old samples */
    for (n = NCoef; n > 0; n--) {
        x[i][n] = x[i][n - 1];
        y[i][n] = y[i][n - 1];
    }

    /* Calculate the new output */
    x[i][0] = NewSample;
    y[i][0] = ACoef[0] * x[i][0];
    for (n = 1; n <= NCoef; n++)
        y[i][0] += ACoef[n] * x[i][n] - BCoef[n] * y[i][n];

    return y[i][0];
}

/* fc=56Hz */
static inline float
adgold_pseudo_stereo_iir(float NewSample)
{
    float ACoef[NCoef + 1] = {
        0.00001409030866231767,
        0.00002818061732463533,
        0.00001409030866231767
    };

    float BCoef[NCoef + 1] = {
        1.00000000000000000000,
        -1.98733021473466760000,
        0.98738361004063568000
    };

    static float y[NCoef + 1]; /* output samples */
    static float x[NCoef + 1]; /* input samples */
    int          n;

    /* shift the old samples */
    for (n = NCoef; n > 0; n--) {
        x[n] = x[n - 1];
        y[n] = y[n - 1];
    }

    /* Calculate the new output */
    x[0] = NewSample;
    y[0] = ACoef[0] * x[0];
    for (n = 1; n <= NCoef; n++)
        y[0] += ACoef[n] * x[n] - BCoef[n] * y[n];

    return y[0];
}

/* fc=3.2kHz - probably incorrect */
static inline float
dss_iir(float NewSample)
{
    float ACoef[NCoef + 1] = {
        0.03356837051492005100,
        0.06713674102984010200,
        0.03356837051492005100
    };

    float BCoef[NCoef + 1] = {
        1.00000000000000000000,
        -1.41898265221812010000,
        0.55326988968868285000
    };

    static float y[NCoef + 1]; /* output samples */
    static float x[NCoef + 1]; /* input samples */
    int          n;

    /* shift the old samples */
    for (n = NCoef; n > 0; n--) {
        x[n] = x[n - 1];
        y[n] = y[n - 1];
    }

    /* Calculate the new output */
    x[0] = NewSample;
    y[0] = ACoef[0] * x[0];
    for (n = 1; n <= NCoef; n++)
        y[0] += ACoef[n] * x[n] - BCoef[n] * y[n];

    return y[0];
}

#undef NCoef
#define NCoef 1
/*Basic high pass to remove DC bias. fc=10Hz*/
static inline float
dac_iir(int i, float NewSample)
{
    float ACoef[NCoef + 1] = {
        0.99901119820285345000,
        -0.99901119820285345000
    };

    float BCoef[NCoef + 1] = {
        1.00000000000000000000,
        -0.99869185905052738000
    };

    static float y[2][NCoef + 1]; /* output samples */
    static float x[2][NCoef + 1]; /* input samples */
    int          n;

    /* shift the old samples */
    for (n = NCoef; n > 0; n--) {
        x[i][n] = x[i][n - 1];
        y[i][n] = y[i][n - 1];
    }

    /* Calculate the new output */
    x[i][0] = NewSample;
    y[i][0] = ACoef[0] * x[i][0];
    for (n = 1; n <= NCoef; n++)
        y[i][0] += ACoef[n] * x[i][n] - BCoef[n] * y[i][n];

    return y[i][0];
}

#undef NCoef
#define NCoef 2

/* One channel of one of the 2-pole IIR filters below: its last inputs and
   outputs. The *_s() forms take the caller's; the others keep 6 x 2 of their
   own, shared by every card that passes the same c and i. */
typedef struct iir2_t {
    double x[NCoef + 1];
    double y[NCoef + 1];
} iir2_t;

static inline double
iir2_step(iir2_t *f, const double *ACoef, const double *BCoef, double NewSample)
{
    int n;

    /* shift the old samples */
    for (n = NCoef; n > 0; n--) {
        f->x[n] = f->x[n - 1];
        f->y[n] = f->y[n - 1];
    }

    /* Calculate the new output */
    f->x[0] = NewSample;
    f->y[0] = ACoef[0] * f->x[0];
    for (n = 1; n <= NCoef; n++)
        f->y[0] += ACoef[n] * f->x[n] - BCoef[n] * f->y[n];

    return f->y[0];
}

/* fc=350Hz */
static const double low_iir_a[NCoef + 1] = {
    0.00049713569693400649,
    0.00099427139386801299,
    0.00049713569693400649
};
static const double low_iir_b[NCoef + 1] = {
    1.00000000000000000000,
    -1.93522955470669530000,
    0.93726236021404663000
};

static inline double
low_iir_s(iir2_t *f, double NewSample)
{
    return iir2_step(f, low_iir_a, low_iir_b, NewSample);
}

static inline double
low_iir(int c, int i, double NewSample)
{
    static iir2_t f[6][2];

    return low_iir_s(&f[c][i], NewSample);
}

/* fc=350Hz */
static const double low_cut_iir_a[NCoef + 1] = {
    0.96839970114733542000,
    -1.93679940229467080000,
    0.96839970114733542000
};
static const double low_cut_iir_b[NCoef + 1] = {
    1.00000000000000000000,
    -1.93522955471202770000,
    0.93726236021916731000
};

static inline double
low_cut_iir_s(iir2_t *f, double NewSample)
{
    return iir2_step(f, low_cut_iir_a, low_cut_iir_b, NewSample);
}

static inline double
low_cut_iir(int c, int i, double NewSample)
{
    static iir2_t f[6][2];

    return low_cut_iir_s(&f[c][i], NewSample);
}

/* fc=3.5kHz */
static const double high_iir_a[NCoef + 1] = {
    0.72248704753064896000,
    -1.44497409506129790000,
    0.72248704753064896000
};
static const double high_iir_b[NCoef + 1] = {
    1.00000000000000000000,
    -1.36640781670578510000,
    0.52352474706139873000
};

static inline double
high_iir_s(iir2_t *f, double NewSample)
{
    return iir2_step(f, high_iir_a, high_iir_b, NewSample);
}

static inline double
high_iir(int c, int i, double NewSample)
{
    static iir2_t f[6][2];

    return high_iir_s(&f[c][i], NewSample);
}

/* fc=3.5kHz */
static const double high_cut_iir_a[NCoef + 1] = {
    0.03927726802250377400,
    0.07855453604500754700,
    0.03927726802250377400
};
static const double high_cut_iir_b[NCoef + 1] = {
    1.00000000000000000000,
    -1.36640781666419950000,
    0.52352474703279628000
};

static inline double
high_cut_iir_s(iir2_t *f, double NewSample)
{
    return iir2_step(f, high_cut_iir_a, high_cut_iir_b, NewSample);
}

static inline double
high_cut_iir(int c, int i, double NewSample)
{
    static iir2_t f[6][2];

    return high_cut_iir_s(&f[c][i], NewSample);
}

/* fc=5.283kHz, gain=-9.477dB, width=0.4845 */
static inline double
deemph_iir(int i, double NewSample)
{
    double ACoef[NCoef + 1] = {
        0.46035077886318842566,
        -0.28440821191249848754,
        0.03388877229118691936
    };

    double BCoef[NCoef + 1] = {
        1.00000000000000000000,
        -1.05429146278569141337,
        0.26412280202756849290
    };
    static double y[6][NCoef + 1]; /* output samples */
    static double x[6][NCoef + 1]; /* input samples */
    int           n;

    /* shift the old samples */
    for (n = NCoef; n > 0; n--) {
        x[i][n] = x[i][n - 1];
        y[i][n] = y[i][n - 1];
    }

    /* Calculate the new output */
    x[i][0] = NewSample;
    y[i][0] = ACoef[0] * x[i][0];
    for (n = 1; n <= NCoef; n++)
        y[i][0] += ACoef[n] * x[i][n] - BCoef[n] * y[i][n];

    return y[i][0];
}

#undef NCoef
#define NCoef 2

/* fc=3.2kHz */
static inline double
sb_iir(int c, int i, double NewSample)
{
    double ACoef[NCoef + 1] = {
        0.03356837051492005100,
        0.06713674102984010200,
        0.03356837051492005100
    };

    double BCoef[NCoef + 1] = {
        1.00000000000000000000,
        -1.41898265221812010000,
        0.55326988968868285000
    };

    static double y[6][2][NCoef + 1]; /* output samples */
    static double x[6][2][NCoef + 1]; /* input samples */
    int           n;

    /* shift the old samples */
    for (n = NCoef; n > 0; n--) {
        x[c][i][n] = x[c][i][n - 1];
        y[c][i][n] = y[c][i][n - 1];
    }

    /* Calculate the new output */
    x[c][i][0] = NewSample;
    y[c][i][0] = ACoef[0] * x[c][i][0];
    for (n = 1; n <= NCoef; n++)
        y[c][i][0] += ACoef[n] * x[c][i][n] - BCoef[n] * y[c][i][n];

    return y[c][i][0];
}

#undef NCoef
#define NCoef      1
#define SB16_NCoef 51

extern double low_fir_sb16_coef[SB16_NCoef];

/* The SB16 output filter's state: both channels' last inputs. The *_s()
   form takes the caller's; low_fir_sb16() keeps one of its own. */
typedef struct sb16_fir_t {
    double x[2][SB16_NCoef + 1]; // input samples
    int    pos;
} sb16_fir_t;

static inline double
low_fir_sb16_s(sb16_fir_t *f, int i, double NewSample)
{
    double out = 0.0;
    int    n;

    /* Calculate the new output */
    f->x[i][f->pos] = NewSample;

    for (n = 0; n < ((SB16_NCoef + 1) - f->pos) && n < SB16_NCoef; n++)
        out += low_fir_sb16_coef[n] * f->x[i][n + f->pos];
    for (; n < SB16_NCoef; n++)
        out += low_fir_sb16_coef[n] * f->x[i][(n + f->pos) - (SB16_NCoef + 1)];

    if (i == 1) {
        f->pos++;
        if (f->pos > SB16_NCoef)
            f->pos = 0;
    }

    return out;
}

static inline double
low_fir_sb16(int i, double NewSample)
{
    static sb16_fir_t f;

    return low_fir_sb16_s(&f, i, NewSample);
}

extern double low_fir_ess_dac2_coef[SB16_NCoef];

static inline double
low_fir_ess_dac2(int i, double NewSample)
{
    static double x[2][SB16_NCoef + 1]; // input samples
    static int    pos    = 0;
    double        out    = 0.0;
    int           n;

    /* Calculate the new output */
    x[i][pos] = NewSample;

    for (n = 0; n < ((SB16_NCoef + 1) - pos) && n < SB16_NCoef; n++)
        out += low_fir_ess_dac2_coef[n] * x[i][n + pos];
    for (; n < SB16_NCoef; n++)
        out += low_fir_ess_dac2_coef[n] * x[i][(n + pos) - (SB16_NCoef + 1)];

    if (i == 1) {
        pos++;
        if (pos > SB16_NCoef)
            pos = 0;
    }

    return out;
}

extern double low_fir_pas16_coef[SB16_NCoef];

static inline double
low_fir_pas16(const int i, const double NewSample)
{
    static double x[2][SB16_NCoef + 1]; // input samples
    static int    pos = 0;
    double        out = 0.0;
    int           n;

    /* Calculate the new output */
    x[i][pos] = NewSample;

    for (n = 0; n < ((SB16_NCoef + 1) - pos) && n < SB16_NCoef; n++)
        out += low_fir_pas16_coef[n] * x[i][n + pos];
    for (; n < SB16_NCoef; n++)
        out += low_fir_pas16_coef[n] * x[i][(n + pos) - (SB16_NCoef + 1)];

    if (i == 1) {
        pos++;
        if (pos > SB16_NCoef)
            pos = 0;
    }

    return out;
}

#endif /*EMU_FILTERS_H*/
