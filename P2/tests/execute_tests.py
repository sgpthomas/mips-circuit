import csv
from random import getrandbits

def complement(bstr):
    res = ""
    for b in bstr:
        res += ('1' if b == '0' else '0')
    return format(int(res, 2) + 1, 'b')

def twos_to_decimal(bstr):
    res = 0
    for i, b in enumerate(bstr):
        pl = ((2**(len(bstr) - 1 - i)) * int(b, 2))
        res += (-pl if i == 0 else pl)
    return res

def decimal_to_twos(num, bits):
    fstr = '0{}b'.format(bits+1)
    res = ''
    if num < 0:
        res = complement(format(abs(num), fstr))
    else:
        res = format(num, fstr)
    return res[(len(res)-bits):]

def add_twos(a, b, bits):
    s = a + b
    overflow = 0
    if s > 2**(bits-1)-1 or s < -2**(bits-1):
        overflow = 1
    return (s, overflow)

def sub_twos(a, b, bits):
    s = a - b
    overflow = 0
    if s > 2**(bits-1)-1 or s < -2**(bits-1):
        overflow = 1
    return (s, overflow)


def adder_tests(w, num):
    for i in range(num):
        a = twos_to_decimal(format(getrandbits(32), '032b'))
        b = twos_to_decimal(format(getrandbits(32), '032b'))
        (s, v) = add_twos(a, b, 32)

        w.writerows([(decimal_to_twos(a, 32), decimal_to_twos(b, 32), '0010', '00000', decimal_to_twos(s, 32), v)])

def immediate_arithmetic(w, num):
    def f(b, sa):
        a = format(b << sa, '032b')
        if sa != 0:
            return int(a[(len(a)-32):-sa] + (sa * '0'), 2)
        else:
            return int(a[(len(a)-32):], 2)

    # addiu
    for i in range(num):
        a = twos_to_decimal(format(getrandbits(32), '032b'))
        imm = twos_to_decimal(format(getrandbits(32), '032b'))
        (s, _) = add_twos(a, imm, 32)
        write(w, a, 0, 0, 0, '1001001', imm, s, 1)

    # andi, ori, xori, lui
    for i in range(num):
        a = getrandbits(32)
        imm = getrandbits(32)
        c_and = a & imm
        c_or = a | imm
        c_xor = a ^ imm
        write(w, a, 0, 0, 0, '1001100', imm, c_and, 1)
        write(w, a, 0, 0, 0, '1001101', imm, c_or, 1)
        write(w, a, 0, 0, 0, '1001110', imm, c_xor, 1)
        write(w, a, 0, 0, 0, '1001111', imm, f(imm, 16), 1)

def register_arithmetic(w, num):
    # addu, subu
    for _ in range(num):
        a = twos_to_decimal(format(getrandbits(32), '032b'))
        b = twos_to_decimal(format(getrandbits(32), '032b'))
        (s1, _) = add_twos(a, b, 32)
        (s2, _) = sub_twos(a, b, 32)
        write(w, a, b, 0, 0, '0100001', 0, s1, 1)
        write(w, a, b, 0, 0, '0100011', 0, s2, 1)

    def flip(n):
        s = ''
        for c in n:
            s += '0' if c == '1' else '1'
        return s

    # and, or, xor, nor
    for _ in range(num):
        a = getrandbits(32)
        b = getrandbits(32)
        c_and = a & b
        c_or = a | b
        c_xor = a ^ b
        c_nor = flip(decimal_to_twos(a | b, 32))
        write(w, a, b, 0, 0, '0100100', 0, c_and, 1)
        write(w, a, b, 0, 0, '0100101', 0, c_or, 1)
        write(w, a, b, 0, 0, '0100110', 0, c_xor, 1)
        write(w, a, b, 0, 0, '0100111', 0, c_nor, 1)

    # slt, sltu
    for _ in range(num*2):
        a = getrandbits(32)
        b = getrandbits(32)
        signed = getrandbits(1) == 1
        if signed:
            d = 1 if twos_to_decimal(format(a, '032b')) < twos_to_decimal(format(b, '032b')) else 0
            write(w, a, b, 0, 0, '0101010', 0, d, 1)
        else:
            d = 1 if a < b else 0
            write(w, a, b, 0, 0, '0101011', 0, d, 1)

def move(w, num):
    # movn(0001011), movz(0001010)
    for _ in range(num):
        a = getrandbits(32)
        b = getrandbits(1)
        we_n = 0 if b == 0 else 1
        we_z = 1 if b == 0 else 0
        write(w, a, b, 0, 0, '0001011', 0, a, we_n)
        write(w, a, b, 0, 0, '0001010', 0, a, we_z)

def shifts(w, num):
    # left shifting
    def f(b, sa):
        a = format(b << sa, '032b')
        if sa != 0:
            return int(a[(len(a)-32):-sa] + (sa * '0'), 2)
        else:
            return int(a[(len(a)-32):], 2)

    # right shifting
    def g(b, sa, arith):
        a = format(b >> sa, '032b')
        if arith and format(b, '032b')[0] == '1':
            i = 0
            while a[i] != '1':
                a = a.replace('0', '1', 1)
                i += 1
        return a

    # left shifting
    for _ in range(num):
        b = getrandbits(32)
        sa = getrandbits(5)
        d = f(b, sa)
        write(w, 0, b, 0, sa, '0000000', 0, d, 1)

    # left variable shifting
    for _ in range(num):
        a = getrandbits(32)
        b = getrandbits(32)
        d = f(b, int(decimal_to_twos(a, 5), 2))
        write(w, a, b, 0, 0, '0000100', 0, d, 1)

    # right shifting
    for _ in range(num):
        b = getrandbits(32)
        sa = getrandbits(5)
        arith = True if getrandbits(1) == 1 else False
        d = g(b, sa, arith)
        opcode = '0000011' if arith else '0000010'
        write(w, 0, b, 0, sa, opcode, 0, d, 1)

    # right variable shifting
    for _ in range(num):
        a = getrandbits(32)
        b = getrandbits(32)
        arith = True if getrandbits(1) == 1 else False
        d = g(b, int(decimal_to_twos(a, 5), 2), arith)
        opcode = '0000111' if arith else '0000110'
        write(w, a, b, 0, 0, opcode, 0, d, 1)

def jump(w):
    codes = ['1000010', '1000011', '0001000', '0001001', '1000100', '1000101', '1000110', '1000111', '1000001']
    for ctrl in codes:
        write(w, 0, 0, 0, 0, ctrl, 0, 'x'*32, 0)

def mem(w):
    codes = ['1100011', '1100000', '1100100', '1101011', '1101000']
    for ctrl in codes:
        write(w, 0, 0, 0, 0, ctrl, 0, 'x'*32, 0)

count = 0
def write(w, a32, b32, rd5, shamt5, fcn12, imm32, d32, we):
    w.writerows([(a32, b32, rd5, shamt5, decode_fcn(fcn12), imm32, d32, 0, rd5, we)])
    global count
    count += 1

def decode_fcn(bstr):
    arr = []
    for ch in bstr:
        arr.insert(0, int(ch))
    # 1st level
    a = arr[3] & (not arr[5])
    b = (not arr[5]) & (not arr[6]) & arr[0]
    c = arr[1] & (not arr[2]) & arr[3]
    d = arr[0] & arr[1] & arr[2] & arr[3]
    e = (not arr[6]) & (not arr[5]) & arr[2]
    z = (not arr[3]) & (not arr[5]) & arr[6]
    y = (not arr[1]) & arr[3] & (not arr[5]) & (not arr[6])
    x = arr[5] & arr[6]
    # 2nd level
    f = b ^ arr[0]
    g = c & (not arr[5]) & (not arr[6])
    w = z | y
    u = c & (not x)
    v = w | x
    h = a & (not g) & (not w)
    # opcode
    opcode = []
    if v == 1:
        opcode = [0, 0, 0, 0]
    elif e == 1:
        opcode = [b, arr[3], arr[1], arr[3]]
    else:
        opcode = [b, f, arr[1], arr[2]]
    res = [opcode[0], opcode[1], opcode[2], opcode[3], h, u, d, g, e, arr[0], w, x]
    s = ''
    for ch in res:
        s = str(ch) + s
    return s

def main():
    filename = 'execute_tests.txt'

    f = open(filename, 'w')
    writer = csv.writer(f, delimiter = '\t')

    # header
    writer.writerows([('A[32]', 'B[32]', 'rd[5]', 'shamt[5]', 'fcn[12]', 'imm[32]', 'D[32]', 'Bfwd[32]', 'rdo[5]', 'we')])

    immediate_arithmetic(writer, 100)
    register_arithmetic(writer, 100)
    move(writer, 100)
    shifts(writer, 100)
    jump(writer)
    mem(writer)

    f.close()

    global count
    print("Wrote {} tests to {}".format(count, filename))

if __name__ == '__main__':
    main()
