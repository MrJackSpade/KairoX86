#!/usr/bin/env python3
"""SeaBIOS's configuration, without its kconfig host tool (which needs POSIX regex.h and does not
build with the Windows toolchain): evaluates the Kconfig subset SeaBIOS uses and writes the two files
its build reads, as its own kconfig writes them.

  kconfig.py <seabios source> <config fragment> <.config out> <autoconf.h out>

The fragment holds CONFIG_X=y / CONFIG_X=0x10 / "# CONFIG_X is not set" lines; every other symbol
takes its Kconfig default. The subset: bool, int, hex and string symbols; a prompt with an optional
"if"; defaults with an optional "if"; "depends on"; "select ... [if ...]"; choice blocks; menus,
whose "depends on" applies to what they hold; "source"; help text. Anything else fails, and so does a
fragment symbol the Kconfig does not have or that ends up with another value than the fragment's.
"""
import re
import sys
from pathlib import Path


class Symbol:
    def __init__(self, name):
        self.name = name
        self.type = None
        self.prompt = None          # condition the prompt is under (an expression), or None for no prompt
        self.defaults = []          # (value expression, condition)
        self.depends = []           # conditions
        self.selects = []           # (target, condition)
        self.choice = None
        self.value = None


class Choice:
    def __init__(self):
        self.members = []
        self.defaults = []
        self.depends = []
        self.prompt = None


TOKEN = re.compile(r'\s*(&&|\|\||!=|=|!|\(|\)|"[^"]*"|[A-Za-z0-9_]+)')


def parse_expr(text):
    tokens = []
    pos = 0
    text = text.strip()
    while pos < len(text):
        m = TOKEN.match(text, pos)
        if not m:
            raise SystemExit(f"kconfig: can't read expression {text!r}")
        tokens.append(m.group(1))
        pos = m.end()
        while pos < len(text) and text[pos].isspace():
            pos += 1
    at = [0]

    def peek():
        return tokens[at[0]] if at[0] < len(tokens) else None

    def take():
        at[0] += 1
        return tokens[at[0] - 1]

    def primary():
        t = take()
        if t == '!':
            return ('not', primary())
        if t == '(':
            e = orexpr()
            if take() != ')':
                raise SystemExit(f"kconfig: unbalanced parentheses in {text!r}")
            return e
        if peek() in ('=', '!='):
            op = take()
            return ('eq' if op == '=' else 'ne', ('sym', t), ('sym', take()))
        return ('sym', t)

    def andexpr():
        e = primary()
        while peek() == '&&':
            take()
            e = ('and', e, primary())
        return e

    def orexpr():
        e = andexpr()
        while peek() == '||':
            take()
            e = ('or', e, andexpr())
        return e

    e = orexpr()
    if at[0] != len(tokens):
        raise SystemExit(f"kconfig: trailing text in expression {text!r}")
    return e


class Config:
    def __init__(self, root):
        self.root = Path(root)
        self.symbols = {}
        self.order = []
        self.choices = []
        self.read(self.root / "src/Kconfig", [])

    def symbol(self, name):
        if name not in self.symbols:
            self.symbols[name] = Symbol(name)
        return self.symbols[name]

    def read(self, path, outer):
        lines = path.read_text().splitlines()
        menus = [list(outer)]           # the conditions of the menus the current line is in
        current = None                  # the Symbol or Choice the attribute lines belong to
        choice = None
        in_help = False
        help_indent = None
        i = 0
        while i < len(lines):
            raw = lines[i]
            i += 1
            line = raw.split('#', 1)[0].rstrip() if not raw.lstrip().startswith('#') else ''
            if in_help:
                indent = len(raw) - len(raw.lstrip())
                if not raw.strip():
                    continue
                if help_indent is None:
                    help_indent = indent
                if indent >= help_indent and help_indent > 0:
                    continue
                in_help = False
            if not line.strip():
                continue
            words = line.split(None, 1)
            key, rest = words[0], (words[1] if len(words) > 1 else '')
            if key == 'mainmenu':
                continue
            if key == 'source':
                self.read(self.root / rest.strip().strip('"'), menus[-1])
                continue
            if key == 'menu':
                menus.append(list(menus[-1]))
                current = 'menu'
                continue
            if key == 'endmenu':
                menus.pop()
                current = None
                continue
            if key == 'choice':
                choice = Choice()
                choice.depends = list(menus[-1])
                self.choices.append(choice)
                current = choice
                continue
            if key == 'endchoice':
                choice = None
                current = None
                continue
            if key in ('config', 'menuconfig'):
                sym = self.symbol(rest.strip())
                if sym.type is not None:
                    raise SystemExit(f"kconfig: {sym.name} is defined twice")
                sym.depends = list(menus[-1]) + (list(choice.depends) if choice else [])
                if choice:
                    sym.choice = choice
                    choice.members.append(sym)
                self.order.append(sym)
                current = sym
                continue
            if key == 'help':
                in_help = True
                help_indent = None
                continue
            if key == 'depends':
                cond = parse_expr(rest[len('on'):] if rest.startswith('on') else rest)
                if current == 'menu':
                    menus[-1].append(cond)
                elif isinstance(current, (Symbol, Choice)):
                    current.depends.append(cond)
                else:
                    raise SystemExit(f"kconfig: 'depends on' outside a symbol in {path}")
                continue
            if key in ('bool', 'int', 'hex', 'string', 'prompt'):
                if key != 'prompt':
                    if not isinstance(current, Symbol):
                        raise SystemExit(f"kconfig: type outside a symbol in {path}")
                    current.type = key
                text = rest.strip()
                if text:
                    m = re.match(r'"([^"]*)"\s*(?:if\s+(.*))?$', text)
                    if not m:
                        raise SystemExit(f"kconfig: can't read prompt {text!r}")
                    cond = parse_expr(m.group(2)) if m.group(2) else ('const', 2)
                    if isinstance(current, (Symbol, Choice)):
                        current.prompt = cond
                continue
            if key == 'default':
                m = re.match(r'(.*?)(?:\s+if\s+(.*))?$', rest.strip())
                value, cond = m.group(1).strip(), (parse_expr(m.group(2)) if m.group(2) else ('const', 2))
                if isinstance(current, Choice):
                    current.defaults.append((value, cond))
                elif isinstance(current, Symbol):
                    current.defaults.append((value, cond))
                else:
                    raise SystemExit(f"kconfig: default outside a symbol in {path}")
                continue
            if key == 'select':
                m = re.match(r'(\w+)(?:\s+if\s+(.*))?$', rest.strip())
                current.selects.append((m.group(1), parse_expr(m.group(2)) if m.group(2) else ('const', 2)))
                continue
            raise SystemExit(f"kconfig: {path.name}: unknown line {raw!r}")

    # Tristate logic on bools: 0 = n, 2 = y.
    def tri(self, e):
        kind = e[0]
        if kind == 'const':
            return e[1]
        if kind == 'sym':
            name = e[1]
            if name in ('y', 'n'):
                return 2 if name == 'y' else 0
            sym = self.symbols.get(name)
            if sym is None or sym.type != 'bool':
                raise SystemExit(f"kconfig: expression names {name}, which is no bool")
            return 2 if sym.value == 'y' else 0
        if kind == 'not':
            return 2 - self.tri(e[1])
        if kind == 'and':
            return min(self.tri(e[1]), self.tri(e[2]))
        if kind == 'or':
            return max(self.tri(e[1]), self.tri(e[2]))
        if kind in ('eq', 'ne'):
            a, b = (self.value_of(x[1]) for x in (e[1], e[2]))
            return 2 if (a == b) == (kind == 'eq') else 0
        raise SystemExit(f"kconfig: bad expression {e}")

    def value_of(self, name):
        sym = self.symbols.get(name)
        return sym.value if sym else name

    def deps(self, item):
        return min([2] + [self.tri(d) for d in item.depends])

    def evaluate(self, user):
        for sym in self.order:
            sym.value = 'n' if sym.type == 'bool' else ''
        for _ in range(100):
            before = {s.name: s.value for s in self.order}
            selected = {}
            for sym in self.order:
                if sym.type == 'bool' and sym.value == 'y':
                    for target, cond in sym.selects:
                        if self.tri(cond):
                            selected[target] = True
            for choice in self.choices:
                visible = self.deps(choice)
                pick = None
                if visible:
                    members = [m for m in choice.members if self.deps(m)]
                    chosen = [m for m in members if user.get(m.name) == 'y']
                    if chosen:
                        pick = chosen[0]
                    else:
                        for value, cond in choice.defaults:
                            if self.tri(cond) and any(m.name == value and m in members for m in members):
                                pick = self.symbols[value]
                                break
                        if pick is None and members:
                            pick = members[0]
                for m in choice.members:
                    m.value = 'y' if m is pick else 'n'
            for sym in self.order:
                if sym.choice:
                    continue
                deps = self.deps(sym)
                visible = deps and sym.prompt is not None and self.tri(sym.prompt)
                if sym.type == 'bool':
                    value = 0
                    if visible and sym.name in user:
                        value = 2 if user[sym.name] == 'y' else 0
                    else:
                        for v, cond in sym.defaults:
                            if self.tri(cond):
                                value = min(deps, self.tri(parse_expr(v)))
                                break
                    if selected.get(sym.name):
                        value = 2
                    sym.value = 'y' if value else 'n'
                else:
                    value = ''
                    if deps:
                        if visible and sym.name in user:
                            value = user[sym.name]
                        else:
                            for v, cond in sym.defaults:
                                if self.tri(cond):
                                    value = v.strip('"') if sym.type == 'string' else v
                                    break
                    sym.value = value
            if before == {s.name: s.value for s in self.order}:
                return
        raise SystemExit("kconfig: the configuration does not settle")

    def check(self, user):
        for name, want in user.items():
            sym = self.symbols.get(name)
            if sym is None or sym.type is None:
                raise SystemExit(f"kconfig: the fragment sets {name}, which the Kconfig does not have")
            got = sym.value
            if sym.type == 'hex':
                same = int(got or '0', 16) == int(want, 16)
            elif sym.type == 'int':
                same = int(got or '0') == int(want)
            else:
                same = got == want
            if not same:
                raise SystemExit(f"kconfig: the fragment sets {name}={want}, but it is {got!r} (its dependencies)")

    def write(self, config_path, header_path):
        config = ["#", "# Automatically generated by tools/seabios/kconfig.py", "#"]
        header = ["/*", " * Automatically generated by tools/seabios/kconfig.py", " */"]
        for sym in self.order:
            if sym.type == 'bool':
                config.append(f"CONFIG_{sym.name}=y" if sym.value == 'y' else f"# CONFIG_{sym.name} is not set")
                header.append(f"#define CONFIG_{sym.name} {1 if sym.value == 'y' else 0}")
            elif sym.type == 'string':
                config.append(f'CONFIG_{sym.name}="{sym.value}"')
                header.append(f'#define CONFIG_{sym.name} "{sym.value}"')
            elif sym.type == 'hex':
                value = sym.value if sym.value.lower().startswith('0x') else '0x' + (sym.value or '0')
                config.append(f"CONFIG_{sym.name}={value}")
                header.append(f"#define CONFIG_{sym.name} {value}")
            elif sym.type == 'int':
                config.append(f"CONFIG_{sym.name}={sym.value or 0}")
                header.append(f"#define CONFIG_{sym.name} {sym.value or 0}")
            else:
                raise SystemExit(f"kconfig: {sym.name} has no type")
        Path(config_path).write_text("\n".join(config) + "\n", newline="\n")
        Path(header_path).write_text("\n".join(header) + "\n", newline="\n")


def read_fragment(path):
    user = {}
    for line in Path(path).read_text().splitlines():
        line = line.strip()
        m = re.match(r'# CONFIG_(\w+) is not set$', line)
        if m:
            user[m.group(1)] = 'n'
            continue
        if not line or line.startswith('#'):
            continue
        m = re.match(r'CONFIG_(\w+)=(.*)$', line)
        if not m:
            raise SystemExit(f"kconfig: can't read fragment line {line!r}")
        user[m.group(1)] = m.group(2).strip('"')
    return user


def main():
    if len(sys.argv) != 5:
        raise SystemExit(__doc__)
    root, fragment, config_out, header_out = sys.argv[1:]
    cfg = Config(root)
    user = read_fragment(fragment)
    cfg.evaluate(user)
    cfg.check(user)
    cfg.write(config_out, header_out)


if __name__ == '__main__':
    main()
