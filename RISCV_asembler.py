import re
import struct
text_file=0
# Định nghĩa các mã opcode và func3, func7
opcode_map = {
    "add": ("0110011", "000", "0000000"),  # add rd, rs1, rs2
    "sub": ("0110011", "000", "0100000"),  # sub rd, rs1, rs2
    "sll": ("0110011", "001", "0000000"),  # sll rd, rs1, rs2
    "xor": ("0110011", "100", "0000000"),  # xor rd, rs1, rs2
    "srl": ("0110011", "101", "0000000"),  # srl rd, rs1, rs2
    "sra": ("0110011", "101", "0100000"),  # sra rd, rs1, rs2
    "or": ("0110011", "110", "0000000"),   # or rd, rs1, rs2
    "and": ("0110011", "111", "0000000"),  # and rd, rs1, rs2
    "slt": ("0110011", "010", "0000000"),  # slt rd, rs1, rs2
    "sltu": ("0110011", "011", "0000000"), # sltu rd, rs1, rs2
    "lr.d": ("0110011", "011", "0001000"), # lr.d rd, (rs1) *
    "sc.d": ("0110011", "011", "0001100"), # sc.d rd, rs2, (rs1) *
    
    "lb":  ("0000011", "000", ""),         # lb rd, offset(rs1)
    "lh":  ("0000011", "001", ""),         # lh rd, offset(rs1)
    "lw":  ("0000011", "010", ""),         # lw rd, offset(rs1)
    "ld":  ("0000011", "011", ""),         # ld rd, offset(rs1)
    "lbu":  ("0000011", "100", ""),        # lbu rd, offset(rs1)
    "lhu":  ("0000011", "101", ""),        # lhu rd, offset(rs1)
    "addi":  ("0010011", "000", ""),       # addi rd, rs1, imm
    "addiw":  ("0011011", "000", ""),       # addiw rd, rs1, imm
    "slli":  ("0010011", "001", "0000000"),# slli rd, rs1, imm
    "xori":  ("0010011", "100", ""),       # xori rd, rs1, imm
    "srli":  ("0010011", "101", "0000000"),# srli rd, rs1, imm
    "srai":  ("0010011", "101", "0100000"),# srai rd, rs1, imm
    "ori":  ("0010011", "110", ""),        # ori rd, rs1, imm
    "andi":  ("0010011", "111", ""),       # andi rd, rs1, imm
    "jalr":  ("1101111", "", ""),          # jal rsd, imm *
    "slti":  ("0010011", "010", ""),       # slti rd, rs1, imm
    "sltiu":  ("0010011", "011", ""),      # sltiu rd, rs1, imm
    "csrw":   ("1110011", "001", ""),      # csrw csr, rs1
    
    
    "sb":  ("0100011", "000", ""),         # sb rs2, offset(rs1)
    "sh":  ("0100011", "001", ""),         # sh rs2, offset(rs1)
    "sw":  ("0100011", "010", ""),         # sw rs2, offset(rs1)
    "sd":  ("0100011", "010", ""),         # sd rs2, offset(rs1)
    
    "beq":  ("1100011", "000", ""),        # beq rs1, rs2, offset
    "bne":  ("1100011", "001", ""),        # bne rs1, rs2, offset
    "blt":  ("1100011", "100", ""),        # blt rs1, rs2, offset
    "bge":  ("1100011", "101", ""),        # bge rs1, rs2, offset
    "bgeu":  ("1100011", "111", ""),       # bgeu rs1, rs2, offset
    "bltu":  ("1100011", "111", ""),       # bltu rs1, rs2, offset
    
    "lui":  ("0110111", "", ""),           # lui rd, imm
    "jal":  ("1101111", "", ""),           # jal rsd, imm
    "j":  ("1101111", "", ""),             # j label
    
    "csrrw": ("1110011", "001", ""),
    "ecall": ("1110011", "000", "0000000"), # ecall
    "ebreak": ("1110011", "000", "000000000001"),# ebreak
    "sret": ("1110011", "000", "000100000010"),  # sret
    "mret": ("1110011", "000", "001100000010"),  # mret
    "mnret": ("1110011", "000", "011100000010"), # mnret
    "wfi": ("1110011", "000", "000100000101"), # wfi
    "sfence.vma": ("1110011", "000", "0001001") # sfence.vma
}

# Hàm để chuyển đổi lệnh R sang mã nhị phân
def encode_r_type(inst, rd, rs1, rs2):
    opcode, func3, func7 = opcode_map[inst]
    rd_bin = format(rd, '05b')
    rs1_bin = format(rs1, '05b')
    rs2_bin = format(rs2, '05b')
    return func7 + rs2_bin + rs1_bin + func3 + rd_bin + opcode

# Hàm để chuyển đổi lệnh I sang mã nhị phân
def encode_i_type(inst, rd, rs1, imm):
    opcode, func3, func7 = opcode_map[inst]
    rd_bin = format(rd, '05b')
    rs1_bin = format(rs1, '05b')
    if (func7 == "0000000" or func7 == "0100000"):
        imm_bin = format(imm & 0xfff, '05b')  # Chỉ lấy 5 bit cuối
        return func7 + imm_bin + rs1_bin + func3 + rd_bin + opcode
    else:
        imm_bin = format(imm & 0xfff, '012b')  # Chỉ lấy 12 bit cuối
        return  imm_bin + rs1_bin + func3 + rd_bin + opcode

# Hàm để chuyển đổi lệnh S sang mã nhị phân
def encode_s_type(inst, rs2, rs1, imm):
    opcode, func3, _ = opcode_map[inst]
    rs2_bin = format(rs2, '05b')
    rs1_bin = format(rs1, '05b')
    imm_bin2 = format(imm & 0xfff, '05b')  # Chỉ lấy 5 bit cuối
    imm_bin1 = format((imm >> 5) & 0x7F, '07b')  # Lấy 7 bit đầu
    return imm_bin1 + rs2_bin + rs1_bin + func3 + imm_bin2 + opcode

# Hàm để chuyển đổi lệnh U sang mã nhị phân
def encode_u_type(inst, rd, imm):
    # lui rd, imm
    opcode, _, _ = opcode_map[inst]
    rd_bin = format(rd, '05b')
    imm_bin = format(imm & 0xfffff, '020b')  # Chỉ lấy 20 bit cuối
    return imm_bin + rd_bin + opcode

# Hàm để chuyển đổi lệnh B sang mã nhị phân
def encode_b_type(inst, rs1, rs2, imm2):
    imm=imm2//2
    opcode, func3, _ = opcode_map[inst]
    rs1_bin = format(rs1, '05b')
    rs2_bin = format(rs2, '05b')
    imm_bin = format(imm & 0xfff, '012b') # Chỉ lấy 12 bit cuối
    # Phân bố lại các bit cho offset theo quy ước của RISC-V (imm[12|10:5|4:1|11])
    imm_btype = imm_bin[0] + imm_bin[2:8] + imm_bin[8:12] + imm_bin[1]
    # Ghép các trường thành mã nhị phân cho lệnh B-type
    return imm_btype[0] + imm_btype[1:7] + rs2_bin + rs1_bin + func3 + imm_btype[7:] + opcode

# Hàm để chuyển đổi lệnh J sang mã nhị phân
def encode_j_type(inst, rd, imm):
    # Lấy opcode từ bảng ánh xạ (giả sử opcode_map tồn tại)
    opcode, _, _ = opcode_map[inst]
    rd_bin = format(rd, '05b')  # Chuyển rd thành nhị phân 5 bit

    # Chuyển immediate thành nhị phân 21-bit (J-type offset)
    imm_bin = format(imm & 0x1FFFFF, '021b')  # Lấy 21 bit cuối cùng

    # Phân bố các bit cho offset theo quy tắc RISC-V J-type (imm[20|10:1|11|19:12])
    imm_jtype = (
        imm_bin[0]                     # imm[20]
        + imm_bin[10:20]               # imm[10:1]
        + imm_bin[9]                   # imm[11]
        + imm_bin[1:9]                 # imm[19:12]
    )

    # Ghép các trường lại để tạo thành mã nhị phân cho lệnh J-type
    instruction = imm_jtype + rd_bin + opcode

    return instruction


# Hàm chính để dịch lệnh
def assemble(instruction):
    # Loại bỏ các ký tự không mong muốn như dấu phẩy
    instruction = instruction.replace(',', '')
    
    parts = instruction.split()
    inst = parts[0]
    
    #R-type
    if inst in ["add", "sub", "sll", "slt", "sltu", "xor", "srl", "sra", "or", "and"]:
        rd = int(parts[1][1:])  # Lấy số từ "rs1", "rs2".
        rs1 = int(parts[2][1:])
        rs2 = int(parts[3][1:])
        return encode_r_type(inst, rd, rs1, rs2)
    #I-type
    elif inst in ["lb", "lh", "lw", "ld", "lbu", "lhu"]:
        rd = int(parts[1][1:])
        offset, rs1 = parts[2].split('(')
        rs1 = int(rs1[:-1][1:])  # Lấy "x1" từ "(x1)"
        offset = int(offset)
        return encode_i_type(inst, rd, rs1, offset)
    elif inst in ["addi", "slti","slli", "srli", "srai", "sltiu", "xori", "ori", "andi"]:
        rd = int(parts[1][1:])
        rs1 = int(parts[2][1:])
        if 'x' in parts[3]:
            imm = int(parts[3], 16)
        else:
            imm = int(parts[3])
        return encode_i_type(inst, rd, rs1, imm)

    #S-type
    elif inst in ["sb","sh", "sw", "sd"]:
        rs2 = int(parts[1][1:])
        offset, rs1 = parts[2].split('(')
        rs1 = int(rs1[:-1][1:])
        offset = int(offset)
        return encode_s_type(inst, rs2, rs1, offset)
    #U-type
    elif inst in ["lui"]:
        # lui rd, imm
        rd = int(parts[1][1:])
        if 'x' in parts[2]:
            imm = int(parts[2], 16)
        else:
            imm = int(parts[2])
        return encode_u_type(inst, rd, imm)
    #B-type
    elif inst in ["beq", "bne", "blt", "bge", "bltu", "bgeu"]:
        rs1 = int(parts[1][1:])  # Lấy số từ phần "rs1"
        rs2 = int(parts[2][1:])  # Lấy số từ phần "rs2"
        if 'x' in parts[3]:
            imm = int(parts[3], 16)
        else:
            imm = int(parts[3])
        return encode_b_type(inst, rs1, rs2, imm)
    #J-type
    elif inst in ["jal"]:
        rd = int(parts[1][1:])  # Lấy số từ phần "rd"
        if 'x' in parts[2]:
            imm = int(parts[2], 16)
        else:
            imm = int(parts[2])
        return encode_j_type(inst, rd, imm)
    elif inst in ["j"]:
        rd = 0
        imm = int(parts[1])
        return encode_j_type(inst, rd, imm)
    elif inst == "li":
        rd = int(parts[1][1:])  # Lấy số từ "rd"
        imm = int(parts[2], 0)  # Chuyển đổi tự động từ hex hoặc decimal
        if -2048 <= imm <= 2047:  # Trường hợp immediate nằm trong 12-bit
            return encode_i_type("addi", rd, 0, imm)  # li rd, imm → addi rd, x0, imm
        else:  # Trường hợp immediate vượt quá 12-bit
            upper_20 = (imm >> 12) & 0xFFFFF  # Lấy 20 bit cao
            lower_12 = imm & 0xFFF  # Lấy 12 bit thấp

            if lower_12 & (1 << 11):  # Nếu bit thứ 11 của lower_12 = 1, cần tăng upper_20
                upper_20 += 1
            
            lui_code = encode_u_type("lui", rd, upper_20)  # lui rd, upper_20
            addi_code = encode_i_type("addi", rd, rd, lower_12)  # addi rd, rd, lower_12

            return lui_code + '\n' + addi_code
    elif inst == "la":
        rd = int(parts[1][1:])  # Lấy số từ "rd"
        imm = int(parts[2], 0)  # Chuyển đổi tự động từ hex hoặc decimal
        if -2048 <= imm <= 2047:  # Trường hợp immediate nằm trong 12-bit
            return encode_i_type("addi", rd, 0, imm)  # li rd, imm → addi rd, x0, imm
        else:  # Trường hợp immediate vượt quá 12-bit
            upper_20 = (imm >> 12) & 0xFFFFF  # Lấy 20 bit cao
            lower_12 = imm & 0xFFF  # Lấy 12 bit thấp

            if lower_12 & (1 << 11):  # Nếu bit thứ 11 của lower_12 = 1, cần tăng upper_20
                upper_20 += 1
            
            lui_code = encode_u_type("lui", rd, upper_20)  # lui rd, upper_20
            addi_code = encode_i_type("addiw", rd, rd, lower_12)  # addi rd, rd, lower_12

            return lui_code + '\n' + addi_code

    elif inst in ["ecall", "ebreak", "sret", "mret", "mnret", "wfi", "sfence.vma", "csrrw"]:
        if inst == "csrrw":
            rd = int(parts[1][1:])   # Lấy số từ "x5" -> 5
            csr = int(parts[2])# Địa chỉ CSR có thể là số hex (vd: 0x300 -> 768)
            rs1 = int(parts[3][1:])  # Lấy số từ "x10" -> 10

            opcode = "1110011"
            funct3 = "001"

            # Chuyển tất cả các giá trị thành chuỗi nhị phân với số bit tương ứng
            rd_bin = f"{rd:05b}"   # 5-bit
            rs1_bin = f"{rs1:05b}" # 5-bit
            csr_bin = '000' + str(csr)
            # Kết hợp các thành phần theo đúng cấu trúc
            binary_code = csr_bin + rs1_bin + funct3 + rd_bin + opcode
            return binary_code
        if inst == "csrw":
            csr = int(parts[1])# Địa chỉ CSR có thể là số hex (vd: 0x300 -> 768)
            rs1 = int(parts[2][1:])  # Lấy số từ "x10" -> 10

            opcode = "1110011"
            funct3 = "001"

            # Chuyển tất cả các giá trị thành chuỗi nhị phân với số bit tương ứng
            rd_bin = "00000"   # 5-bit
            rs1_bin = f"{rs1:05b}" # 5-bit
            csr_bin = '000' + str(csr)
            # Kết hợp các thành phần theo đúng cấu trúc
            binary_code = csr_bin + rs1_bin + funct3 + rd_bin + opcode
            return binary_code
        if inst == "ecall":
            return "00000000000000000000000001110011"
        elif inst == "ebreak":
            return "00000000000100000000000001110011"
        elif inst == "sret":
            return "00010000001000000000000001110011"
        elif inst == "mret":
            return "00110000001000000000000001110011"
        elif inst == "mnret":
            return "01110000001000000000000001110011"
        elif inst == "wfi":
            return "00010000010100000000000001110011"
        elif inst == "sfence.vma":
            rs1 = format(int(parts[1][1:]), '05b')  # Lấy số từ phần "rs1"
            rs2 = format(int(parts[2][1:]), '05b') # Lấy số từ phần "rs2"
            return "0001001" + rs2 + rs1 + "000000001110011"
    else:
        raise ValueError(f"Unknown instruction: {inst}")

# Hàm đổi tên thanh ghi
def replace_registers(instruction):
    register_map = {
    "zero": "x0", " ra": "x1", "sp": "x2", "gp": "x3", "tp ": "x4",
    "t0": "x5", "t1": "x6", "t2": "x7",
    "s0": "x8", "fp": "x8", "s1": "x9",
    "a0": "x10", "a1": "x11", "a2": "x12", "a3": "x13", "a4": "x14", "a5": "x15",
    "a6": "x16", "a7": "x17",
    "s2": "x18", "s3": "x19", "s4": "x20", "s5": "x21", "s6": "x22", "s7": "x23",
    "s8": "x24", "s9": "x25", "s10": "x26", "s11": "x27",
    "t3": "x28", "t4": "x29", "t5": "x30", "t6": "x31",
    # S-mode Control and Status Registers (CSR) - 11 Registers
    "sstatus": "0100000000",
    "stvec": "0100000101",
    "sip": "0101000100",
    "sie": "0100000100",
    "scounteren": "0100000110",
    "sscratch": "0101000000",
    "sepc": "0101000001",
    "scause": "0101000010",
    "stval": "0101000011",
    "senvcfg": "0100001010",
    "satp": "0110000000",
    }

    for reg, num in register_map.items():
        instruction = instruction.replace(reg, num)

    return instruction

# Bảng địa chỉ nhãn
def build_label_table(input_filename):
    global text_file
    label_table = {}
    current_address = 0  # Địa chỉ bắt đầu
    with open(input_filename, 'r') as infile:
        for line in infile:
            line = line.strip()
            if line.startswith('.text'):
                text_file=1
                continue
            if not line or line.startswith('#'):  # Bỏ qua dòng rỗng hoặc chú thích
                continue
            if text_file == 0 :
                continue
            if line.endswith(':'):  # Nhãn
                label = line[:-1]  # Loại bỏ dấu ":" khỏi nhãn
                label_table[label] = current_address
                
            else:
                current_address += 4  # Tăng địa chỉ hiện tại lên 4 byte cho mỗi lệnh
    return label_table

#Hàm xử lý nhãn trùng
def resolve_labels(line, label_table, current_address):
    for label, address in label_table.items():
        # Tìm kiếm chính xác nhãn bằng regex: r'\b' để xác định ranh giới từ
        pattern = fr'\b{label}\b'
        if re.search(pattern, line):
            # Tính toán offset
            offset = address - current_address
            # Thay thế nhãn bằng offset
            line = re.sub(pattern, str(offset), line)
    return line

def parse_data_section(lines):
    memory = []

    for line in lines:
        line = line.strip()
        if not line or line.startswith('.data'):
            continue

        # Tách nhãn và nội dung
        if ':' in line:
            label, directive = line.split(':', 1)
            directive = directive.strip()
        else:
            directive = line

        # Xử lý từng loại chỉ thị
        if directive.startswith('.word'):
            nums = re.findall(r'-?\d+', directive)
            for num in nums:
                val = int(num)
                memory.extend(struct.pack('<I', val))  # 4 bytes little endian

        elif directive.startswith('.half'):
            nums = re.findall(r'-?\d+', directive)
            for num in nums:
                val = int(num)
                memory.extend(struct.pack('<H', val))  # 2 bytes little endian

        elif directive.startswith('.byte'):
            nums = re.findall(r'0x[0-9a-fA-F]+|\d+', directive)
            for num in nums:
                val = int(num, 0)  # auto-detect base (hex or dec)
                memory.append(val)

        elif directive.startswith('.ascii'):
            match = re.search(r'"(.*)"', directive)
            if match:
                content = match.group(1)
                memory.extend(content.encode('ascii'))

    # Pad to multiple of 4 bytes
    while len(memory) % 4 != 0:
        memory.append(0)

    # Chia thành từng từ 32-bit (4 byte), little endian
    output = []
    for i in range(0, len(memory), 4):
        word = memory[i:i+4]
        word_le = word[::-1]  # Little endian
        binary_str = ''.join(f'{b:08b}' for b in word_le)
        output.append(binary_str)

    return output
# Hàm xử lí file

def assemble_file(input_filename, output_filename, output_filename2):
    global text_file
    # Xây dựng bảng nhãn
    label_table = build_label_table(input_filename)
    text_file = 0
    # Duyệt lại file để dịch lệnh
    current_address = 0  # Địa chỉ bắt đầu
    with open(input_filename, 'r') as infile, open(output_filename, 'w') as outfile:
        for line in infile:
            line = line.strip()
            if line.startswith('.text'):
                text_file=1
                continue
            if text_file == 0 :
                continue
            if not line or line.startswith('#'):  # Bỏ qua dòng rỗng hoặc chú thích
                continue

            if line.endswith(':'):  # Bỏ qua nhãn
                continue
            
            # Thay thế nhãn bằng địa chỉ trong bảng nhãn
            line = resolve_labels(line, label_table, current_address)

            line = replace_registers(line)  # Thay thế tất cả các thanh ghi
            current_address += 4
            
            
            try:
                binary_code = assemble(line)  # Gọi hàm assemble để dịch lệnh
                
                outfile.write( binary_code + '\n')
            except ValueError as e:
                outfile.write(f"Error: {e} -> Line: {line}\n")
                
                
    with open(input_filename, 'r') as infile:
        lines = infile.readlines()

    binary_lines = parse_data_section(lines)

    with open(output_filename2, 'w') as outfile:
        for line in binary_lines:
            outfile.write(line + '\n')

# Sử dụng hàm để đọc từ file "test.asm" và ghi kết quả ra file "binary.bin"
assemble_file("test_label.s", "text.bin", "data.bin")

