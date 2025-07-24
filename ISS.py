from CSR import CSR32, SStatus, STVec, SIE, SIP, SCOUNTEREN, SSCRATCH, SEPC, SCause, STval, SENVCFG, SATP
class RISCV_ISS:
    def __init__(self, mem_size=4096):
        self.regs = [0] * 32
        self.pc = 0x0
        self.memory = bytearray(mem_size)
        self.privilege_level = 0b00  # 00: user, 01: supervisor
        self.csrs = {
            "sstatus": SStatus(),
            "stvec": STVec(),
            "sie": SIE(),
            "sip": SIP(),
            "scounteren": SCOUNTEREN(),
            "sscratch": SSCRATCH(),
            "sepc": SEPC(),
            "scause": SCause(),
            "stval": STval(),
            "senvcfg": SENVCFG(),
            "satp": SATP(),
        }
        
    def load_program_from_binary_file(self, filepath, base_address=0x0):
        with open(filepath, "r") as f:
            lines = f.readlines()

        address = base_address
        for line in lines:
            binary_str = line.strip()
            if len(binary_str) != 32 or not all(c in "01" for c in binary_str):
                raise ValueError(f"Invalid binary line: {binary_str}")
            
            # Chuyển binary string thành số nguyên
            instruction = int(binary_str, 2)

            # Ghi vào memory (little-endian 4 bytes)
            self.memory[address + 0] = instruction & 0xFF
            self.memory[address + 1] = (instruction >> 8) & 0xFF
            self.memory[address + 2] = (instruction >> 16) & 0xFF
            self.memory[address + 3] = (instruction >> 24) & 0xFF

            address += 4  # mỗi instruction 4 byte
            
    def dump_loaded_instructions(self, base_address=0x0, count=None):
        """
        Đọc và hiển thị các instruction đã load từ bộ nhớ.
        
        Args:
            base_address: Địa chỉ bắt đầu đọc.
            count: Số lượng lệnh cần đọc (nếu None, đọc đến hết vùng không rỗng).
        """
        address = base_address
        instructions = []

        while True:
            if address + 3 >= len(self.memory):
                break  # vượt giới hạn bộ nhớ

            # Đọc 4 byte (little endian)
            b0 = self.memory[address]
            b1 = self.memory[address + 1]
            b2 = self.memory[address + 2]
            b3 = self.memory[address + 3]

            instr = (b3 << 24) | (b2 << 16) | (b1 << 8) | b0
            instructions.append((address, instr))

            address += 4
            if count is not None and len(instructions) >= count:
                break
            if instr == 0:
                break  # coi 0 là kết thúc chương trình nếu không xác định count

        # In ra
        for addr, instr in instructions:
            print(f"{addr:08X}: {instr:032b}")

    def read_reg(self, idx):
        return self.regs[idx]

    def write_reg(self, idx, val):
        if idx != 0:
            self.regs[idx] = val  # x0 luôn bằng 0 theo RISC-V
            
    def write_info(self):
        a = input("Nhập giá trị sstatus (chuỗi nhị phân 32 bit): ")
        self.csrs["sstatus"].write(a)

    def display_info(self):
        print("Giá trị hiện tại của sstatus:", self.csrs["sstatus"].read())
    
    # Đọc từ bộ nhớ
    def load_byte(self, addr):
        return self.memory[addr]

    def load_halfword(self, addr):
        return self.memory[addr] | (self.memory[addr + 1] << 8)

    def load_word(self, addr):
        return (
            self.memory[addr] |
            (self.memory[addr + 1] << 8) |
            (self.memory[addr + 2] << 16) |
            (self.memory[addr + 3] << 24)
        )

    # Ghi vào bộ nhớ
    def store_byte(self, addr, value):
        self.memory[addr] = value & 0xFF

    def store_halfword(self, addr, value):
        self.memory[addr] = value & 0xFF
        self.memory[addr + 1] = (value >> 8) & 0xFF

    def store_word(self, addr, value):
        self.memory[addr] = value & 0xFF
        self.memory[addr + 1] = (value >> 8) & 0xFF
        self.memory[addr + 2] = (value >> 16) & 0xFF
        self.memory[addr + 3] = (value >> 24) & 0xFF

    def step(self):
        instr = self.load_word(self.pc)
        self.pc += 4

        opcode = instr & 0x7F

        # Dispatch theo opcode
        if opcode == 0b0110011:
            self.execute_rtype(instr)
        elif opcode == 0b0010011:
            self.execute_itype(instr)
        elif opcode == 0b0000011:
            self.execute_load(instr)
        elif opcode == 0b0100011:
            self.execute_store(instr)
        elif opcode == 0b1100011:
            self.execute_btype(instr)
        elif opcode in ("0110111", "0010111"):
            self.execute_utype(instr)
        elif opcode == 0b1101111:
            self.execute_jtype(instr)
        elif instr == 0:
            print("Simulation completed!")
            exit()
        else:
            raise NotImplementedError(f"Unknown opcode: {opcode:07b}")

    def sign_extend(self, val, bits):
        if (val >> (bits - 1)) & 1:
            return val | (~0 << bits)
        else:
            return val & ((1 << bits) - 1)

    def execute_rtype(self, instr):
        rd     = (instr >> 7) & 0x1F
        funct3 = (instr >> 12) & 0x07
        rs1    = (instr >> 15) & 0x1F
        rs2    = (instr >> 20) & 0x1F
        funct7 = (instr >> 25) & 0x7F

        mnemonic = "unknown"

        if funct3 == 0b000 and funct7 == 0b0000000:
            # ADD
            result = self.regs[rs1] + self.regs[rs2]
            mnemonic = "add"
        elif funct3 == 0b000 and funct7 == 0b0100000:
            # SUB
            result = self.regs[rs1] - self.regs[rs2]
            mnemonic = "sub"
        elif funct3 == 0b001:
            # SLL
            shamt = self.regs[rs2] & 0b11111
            result = (self.regs[rs1] << shamt) & 0xFFFFFFFF
            mnemonic = "sll"
        elif funct3 == 0b010:
            # SLT
            result = 1 if self.regs[rs1] < self.regs[rs2] else 0
            mnemonic = "slt"
        elif funct3 == 0b011:
            # SLTU (unsigned)
            result = 1 if (self.regs[rs1] & 0xFFFFFFFF) < (self.regs[rs2] & 0xFFFFFFFF) else 0
            mnemonic = "sltu"
        elif funct3 == 0b100:
            # XOR
            result = self.regs[rs1] ^ self.regs[rs2]
            mnemonic = "xor"
        elif funct3 == 0b101 and funct7 == 0b0000000:
            # SRL
            shamt = self.regs[rs2] & 0b11111
            result = (self.regs[rs1] >> shamt) & 0xFFFFFFFF
            mnemonic = "srl"
        elif funct3 == 0b101 and funct7 == 0b0100000:
            # SRA (arith)
            shamt = self.regs[rs2] & 0b11111
            result = (self.regs[rs1] >> shamt) if self.regs[rs1] & 0x80000000 == 0 else ((self.regs[rs1] | (~0xFFFFFFFF)) >> shamt)
            mnemonic = "sra"
        elif funct3 == 0b110:
            # OR
            result = self.regs[rs1] | self.regs[rs2]
            mnemonic = "or"
        elif funct3 == 0b111:
            # AND
            result = self.regs[rs1] & self.regs[rs2]
            mnemonic = "and"
        else:
            raise NotImplementedError(f"Unknown R-type instruction: funct3={funct3:03b}, funct7={funct7:07b}")

        self.write_reg(rd, result)
        print(f"Executed: {mnemonic} x{rd}, x{rs1}, x{rs2}")

    def execute_itype(self, instr):
        rd     = (instr >> 7) & 0x1F
        funct3 = (instr >> 12) & 0x07
        rs1    = (instr >> 15) & 0x1F
        imm    = (instr >> 20) & 0xFFF
        mnemonic = "unknown"

        # Ký hiệu để xử lý số âm (12-bit signed immediate)
        if imm & 0x800:
            imm -= 0x1000  # sign-extend 12-bit

        if funct3 == 0b000:  # ADDI
            result = self.regs[rs1] + imm
            mnemonic = "addi"
        elif funct3 == 0b111:  # ANDI
            result = self.regs[rs1] & imm
            mnemonic = "andi"
        elif funct3 == 0b100:  # XORI
            result = self.regs[rs1] ^ imm
            mnemonic = "xori"
        elif funct3 == 0b010:  # SLTI
            result = 1 if self.regs[rs1] < imm else 0
            mnemonic = "slti"
        elif funct3 == 0b011:  # SLTIU
            result = 1 if (self.regs[rs1] & 0xFFFFFFFF) < (imm & 0xFFFFFFFF) else 0
            mnemonic = "sltiu"
        elif funct3 == 0b001:  # SLLI
            shamt = imm & 0x1F
            result = (self.regs[rs1] << shamt) & 0xFFFFFFFF
            mnemonic = "slli"
        elif funct3 == 0b101:
            shamt = imm & 0x1F
            funct7 = (instr >> 25) & 0x7F
            if funct7 == 0b0000000:
                result = (self.regs[rs1] >> shamt) & 0xFFFFFFFF
                mnemonic = "srli"
            elif funct7 == 0b0100000:
                # SRAI: toán tử shift dấu
                val = self.regs[rs1]
                if val & 0x80000000:
                    result = (val | (~0xFFFFFFFF)) >> shamt
                else:
                    result = val >> shamt
                mnemonic = "srai"
            else:
                raise NotImplementedError(f"Unknown shift variant funct7={funct7:07b}")
        elif funct3 == 0b110:  # ORI
            result = self.regs[rs1] | imm
            mnemonic = "ori"
        else:
            raise NotImplementedError(f"Unknown I-type instruction: funct3={funct3:03b}")

        self.write_reg(rd, result)
        print(f"Executed: {mnemonic} x{rd}, x{rs1}, {imm}")

    def execute_load(self, instr):
        rd     = (instr >> 7) & 0x1F
        funct3 = (instr >> 12) & 0x07
        rs1    = (instr >> 15) & 0x1F
        imm    = self.sign_extend((instr >> 20) & 0xFFF, 12)
        addr   = (self.regs[rs1] + imm) & 0xFFFFFFFF

        if addr % 4 != 0:
            self.raise_exception("Load address misaligned", addr)
            return

        if funct3 == 0b000:  # lb
            val = self.memory[addr]
            val = self.sign_extend(val, 8)
        elif funct3 == 0b001:  # lh
            val = self.memory[addr] | (self.memory[addr+1] << 8)
            val = self.sign_extend(val, 16)
        elif funct3 == 0b010:  # lw
            val = 0
            for i in range(4):
                val |= self.memory[addr+i] << (8 * i)
            val = self.sign_extend(val, 32)
        elif funct3 == 0b100:  # lbu
            val = self.memory[addr]
        elif funct3 == 0b101:  # lhu
            val = self.memory[addr] | (self.memory[addr+1] << 8)
        else:
            raise NotImplementedError(f"Unsupported load funct3: {funct3}")

        self.write_reg(rd, val)

    def execute_store(self, instr):
        funct3 = (instr >> 12) & 0x07
        rs1 = (instr >> 15) & 0x1F
        rs2 = (instr >> 20) & 0x1F
        imm = ((instr >> 25) << 5) | ((instr >> 7) & 0x1F)
        imm = self.sign_extend(imm, 12)
        addr = (self.regs[rs1] + imm) & 0xFFFFFFFF
        val = self.regs[rs2]

        if addr % 4 != 0:
            self.raise_exception("Store/AMO address misaligned", addr)
            return
        
        if funct3 == 0b000:  # sb
            self.memory[addr] = val & 0xFF
        elif funct3 == 0b001:  # sh
            self.memory[addr] = val & 0xFF
            self.memory[addr+1] = (val >> 8) & 0xFF
        elif funct3 == 0b010:  # sw
            for i in range(4):
                self.memory[addr + i] = (val >> (8 * i)) & 0xFF
        elif funct3 == 0b011:  # sd (RV64 only)
            for i in range(8):
                self.memory[addr + i] = (val >> (8 * i)) & 0xFF
        else:
            raise NotImplementedError(f"Unsupported store funct3: {funct3}")

    def execute_btype(self, instr):
        rs1    = (instr >> 15) & 0x1F
        rs2    = (instr >> 20) & 0x1F
        funct3 = (instr >> 12) & 0x07

        # Tách các trường immediate trong B-type: imm[12|10:5|4:1|11] + '0'
        imm_12   = (instr >> 31) & 0x1
        imm_10_5 = (instr >> 25) & 0x3F
        imm_4_1  = (instr >> 8) & 0xF
        imm_11   = (instr >> 7) & 0x1

        # Ghép lại thành immediate 13-bit
        imm = (imm_12 << 12) | (imm_11 << 11) | (imm_10_5 << 5) | (imm_4_1 << 1)
        imm = self.sign_extend(imm, 13)  # Dịch thành số có dấu

        rs1_val = self.regs[rs1]
        rs2_val = self.regs[rs2]
        taken = False
        mnemonic = "unknown"

        if funct3 == 0b000:  # beq
            if rs1_val == rs2_val:
                self.pc += imm
                taken = True
            mnemonic = "beq"
        elif funct3 == 0b001:  # bne
            if rs1_val != rs2_val:
                self.pc += imm
                taken = True
            mnemonic = "bne"
        elif funct3 == 0b100:  # blt
            if rs1_val < rs2_val:
                self.pc += imm
                taken = True
            mnemonic = "blt"
        elif funct3 == 0b101:  # bge
            if rs1_val >= rs2_val:
                self.pc += imm
                taken = True
            mnemonic = "bge"
        elif funct3 == 0b110:  # bltu
            if (rs1_val & 0xFFFFFFFF) < (rs2_val & 0xFFFFFFFF):
                self.pc += imm
                taken = True
            mnemonic = "bltu"
        elif funct3 == 0b111:  # bgeu
            if (rs1_val & 0xFFFFFFFF) >= (rs2_val & 0xFFFFFFFF):
                self.pc += imm
                taken = True
            mnemonic = "bgeu"

        # Nếu không nhảy, tăng PC như bình thường (giả sử PC đã bị cập nhật sau lệnh fetch)
        if taken:
            self.pc -= 4

        print(f"Executed: {mnemonic} x{rs1}, x{rs2}, {imm}")

    def execute_utype(self, instr):
        opcode = instr & 0x7F            # opcode = bits [6:0]
        rd     = (instr >> 7) & 0x1F     # rd     = bits [11:7]
        imm    = instr >> 12             # imm    = bits [31:12]
        mnemonic = "unknown"

        if opcode == 0b0110111:  # LUI
            self.regs[rd] = imm << 12
            mnemonic = "lui"
        elif opcode == 0b0010111:  # AUIPC
            self.regs[rd] = self.pc + (imm << 12)
            mnemonic = "auipc"

        print(f"Executed: {mnemonic} x{rd}, {imm}")
        return f"{mnemonic} x{rd}, {imm}"

    def execute_jtype(self, instr):
        opcode = instr & 0x7F            # bits [6:0]
        rd     = (instr >> 7) & 0x1F     # bits [11:7]

        # immediate: [20|10:1|11|19:12] << 1
        imm_20   = (instr >> 31) & 0x1
        imm_10_1 = (instr >> 21) & 0x3FF
        imm_11   = (instr >> 20) & 0x1
        imm_19_12= (instr >> 12) & 0xFF

        imm = (imm_20 << 20) | (imm_19_12 << 12) | (imm_11 << 11) | (imm_10_1 << 1)
        imm = self.sign_extend(imm, 21)

        if opcode == 0b1101111:  # JAL
            self.regs[rd] = self.pc + 4
            self.pc += imm
            return f"jal x{rd}, {imm}"

        return "unknown"

    def raise_exception(self, cause_description, faulting_address=None):
        self.csrs["scause"].set_cause_by_description(cause_description)
        self.csrs["sepc"].write(self.pc)

        if faulting_address is not None:
            self.csrs["stval"].write(faulting_address)

        # Jump to handler address in stvec
        stvec = self.csrs["stvec"].read()
        self.pc = stvec
        self.privilege_level = 0b01  # Chuyển vào Supervisor Mode

        print(f"Trap: {cause_description}, pc set to {hex(self.pc)}")

    def handle_ecall(self):
        if self.privilege_level == 0:
            self.raise_exception("Environment call from U-mode")
        elif self.privilege_level == 1:
            self.raise_exception("Environment call from S-mode")

    def handle_sret(self):
        self.pc = self.csrs["sepc"].read()
        self.privilege_level = 0b00  # Giả sử quay về user mode
        print("Return from supervisor mode to user mode")
