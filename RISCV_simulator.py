# RISC-V Instruction Set Simulator in Python
# Data Structures
from Debug_Module import DebugModule
registerFiles = {f"{i}": 0 for i in range(32)}  # Register file without 'x'\
dataMemory = {}  # Data memory
IO = {}
stack = []
debug_mode = False
pc = 0  # Program counter
handler_base_addr = "10000000000000000010100101100000" # Địa chỉ base handler
ECALL = {
    "PRINT_INT": 1,
    "PRINT_FLOAT": 2,
    "PRINT_DOUBLE": 3,
    "PRINT_STRING": 4,
    "READ_INT": 5,
    "READ_FLOAT": 6,
    "READ_DOUBLE": 7,
    "READ_STRING": 8,
    "SBRK": 9,
    "EXIT": 10,
    "PRINT_CHAR": 11,
    "READ_CHAR": 12,
    "OPEN_FILE": 13,
    "READ_FILE": 14,
    "WRITE_FILE": 15,
    "CLOSE_FILE": 16
}

SSTATUS_SIE_BIT = 1
SSTATUS_SPIE_BIT = 5
SSTATUS_UBE_BIT = 6
SSTATUS_SPP_BIT = 8
SSTATUS_SUM_BIT = 18
SSTATUS_MXR_BIT = 19
SUPERVISOR_MODE = True
# Global DCSR bit positions
# Global DCSR bit positions (based on updated bit layout)
DCSR_PRV0_BIT         = 0
DCSR_PRV1_BIT         = 1
DCSR_STEP_BIT         = 2
DCSR_NMIP_BIT         = 3
DCSR_MPRVEN_BIT       = 4
DCSR_V_BIT            = 5
DCSR_CAUSE0_BIT       = 6
DCSR_CAUSE1_BIT       = 7
DCSR_CAUSE2_BIT       = 8
DCSR_STOPTIME_BIT     = 9
DCSR_STOPCOUNT_BIT    = 10
DCSR_STEP_IE_BIT      = 11
DCSR_EBREAKU_BIT      = 12
DCSR_EBREAKS_BIT      = 13
DCSR_EBREAKM_BIT      = 14
DCSR_EBREAKVS_BIT     = 15
DCSR_EBREAKVU_BIT     = 16
DCSR_PELP_BIT         = 17
DCSR_CETRIG_BIT       = 18
# Bit 19 = 0
DCSR_EXTCAUSE0_BIT    = 24
DCSR_EXTCAUSE1_BIT    = 25
DCSR_EXTCAUSE2_BIT    = 26
# Bit 27 = 0
DCSR_DEBUGVER0_BIT    = 28
DCSR_DEBUGVER1_BIT    = 29
DCSR_DEBUGVER2_BIT    = 30
DCSR_DEBUGVER3_BIT    = 31


Instruction_address_misaligned = 0
Instruction_access_fault = 1
Illegal_instruction = 2
Breakpoint = 3
Load_address_misaligned = 4
Load_access_fault = 5
StoreAMO_address_misaligned = 6
StoreAMO_access_fault = 7
Environment_call_from_Umode = 8
Environment_call_from_Smode = 9
Instruction_page_fault = 12
Load_page_fault = 13
StoreAMO_page_fault= 15

class CSR32:
    def __init__(self, name, reset_value="0" * 32):
        self.name = name
        self.value = reset_value  # Chuỗi nhị phân 32 bit
        self.important_bits = {}  # Các bit đặc biệt và tác dụng của chúng
    
    def write(self, binary_string):
        if len(binary_string) != 32 or not all(c in "01" for c in binary_string):
            raise ValueError("Input must be a 32-bit binary string.")
        self.value = binary_string
    
    def read(self):
        return self.value
    
    def set_important_bits(self, bit_info):
        """ Thiết lập các bit quan trọng với mô tả tác dụng của chúng. """
        self.important_bits = {bit: desc for bit, desc in bit_info.items() if 0 <= bit < 32}
    
    def check_important_bits(self):
        """ Kiểm tra và báo hiệu các bit quan trọng đang được kích hoạt. """
        active_bits = [f"Bit {bit}: {desc}" for bit, desc in self.important_bits.items() if self.value[31 - bit] == '1']
        return "\n".join(active_bits) if active_bits else "No important bits set."
    
    def activate_bit(self, bit_position):
        """ Đặt một bit quan trọng về 1 khi nó được kích hoạt. """
        if bit_position in self.important_bits:
            bit_list = list(self.value)
            bit_list[31 - bit_position] = '1'  # Đặt bit tại vị trí mong muốn
            self.value = "".join(bit_list)
        else:
            raise ValueError(f"Bit {bit_position} không có tác dụng đặc biệt trong {self.name}")

    def activate_by_name(self, description):
        """ Kích hoạt bit quan trọng bằng mô tả của nó. """
        for bit, desc in self.important_bits.items():
            if desc.lower() == description.lower():  # So sánh không phân biệt hoa thường
                self.activate_bit(bit)
                return
        raise ValueError(f"Không tìm thấy mô tả '{description}' trong {self.name}")
# Các thanh ghi của S-mode
class SStatus(CSR32):
    # Các bit WPRI (không được phép thay đổi)
    WPRI_BITS = (
        list(range(20, 31)) +  # Bits 20–30
        [17, 11, 7, 4, 3, 2, 0]  # Các bit riêng lẻ
    )

    def __init__(self):
        super().__init__("sstatus")
        self.set_important_bits({
            SSTATUS_SIE_BIT: "SIE - Cho phép ngắt ở chế độ Supervisor",
            SSTATUS_SPIE_BIT: "SPIE - Lưu trạng thái SIE trước khi vào trap",
            SSTATUS_UBE_BIT: "UBE - Bộ nhớ ở chế độ User sử dụng kiểu Big-Endian",
            SSTATUS_SPP_BIT: "SPP - Lưu chế độ đặc quyền trước khi vào trap là Supervisor",
            SSTATUS_SUM_BIT: "SUM - Cho phép Supervisor truy cập bộ nhớ User",
            SSTATUS_MXR_BIT: "MXR - Cho phép đọc cả trang có cờ thực thi"
        })

    def handle_exception(self):
        print(f"Exception: Illegal write to WPRI bits in {self.name}")

    def check_invalid_write(self, new_binary_string):
        """Kiểm tra nếu ghi sai vào các bit WPRI."""
        for bit in self.WPRI_BITS:
            old_bit = self.value[31 - bit]
            new_bit = new_binary_string[31 - bit]
            if old_bit != new_bit:
                self.handle_exception()
                break  # Có vi phạm thì dừng luôn, không cần kiểm thêm

    def write(self, binary_string):
        if len(binary_string) != 32 or not all(c in "01" for c in binary_string):
            raise ValueError("Input must be a 32-bit binary string.")
        self.check_invalid_write(binary_string)
        self.value = binary_string
class STVec(CSR32):
    def __init__(self):
        super().__init__("stvec")
        self.set_important_bits({
            0: "Mode bit 0",
            1: "Mode bit 1"
        })

    @property
    def mode(self):
        """Trả về chế độ định tuyến trap: 0 (Direct) hoặc 1 (Vectored)"""
        val = int(self.read(), 2)
        return val & 0b11  # 2 bit thấp nhất

    @property
    def base(self):
        """Trả về địa chỉ cơ sở BASE trong stvec (bỏ 2 bit thấp nhất)"""
        val = int(self.read(), 2)
        return val & ~0b11  # Clear 2 bit thấp nhất

    def set_pc(self, scause_code):
        """
        Tính địa chỉ PC handler dựa vào giá trị stvec và scause.
        """
        if self.mode == 1:
            return self.base + 4 * scause_code  # vectored
        else:
            return self.base  # direct
class SIE(CSR32):
    # Các bit WPRI trong SIE (bits 31–12)
    WPRI_BITS = list(range(12, 32))

    def __init__(self):
        super().__init__("sie")
        self.set_important_bits({
            1: "SSIE - Supervisor Software Interrupt Enable",
            5: "STIE - Supervisor Timer Interrupt Enable",
            9: "SEIE - Supervisor External Interrupt Enable",
            13: "LCOFIE - Local Core Overflow Interrupt Enable"
        })

    def handle_exception(self):
        print(f"Exception: Illegal write to WPRI bits in {self.name}")

    def check_invalid_write(self, new_binary_string):
        """Kiểm tra nếu ghi sai vào các bit WPRI."""
        for bit in self.WPRI_BITS:
            old_bit = self.value[31 - bit]
            new_bit = new_binary_string[31 - bit]
            if old_bit != new_bit:
                self.handle_exception()
                break

    def write(self, binary_string):
        if len(binary_string) != 32 or not all(c in "01" for c in binary_string):
            raise ValueError("Input must be a 32-bit binary string.")
        self.check_invalid_write(binary_string)
        self.value = binary_string
class SIP(CSR32):
    # Các bit WPRI trong SIP (bits 31–12)
    WPRI_BITS = list(range(12, 32))

    def __init__(self):
        super().__init__("sip")
        self.set_important_bits({
            1: "SSIP - Supervisor Software Interrupt Pending",
            5: "STIP - Supervisor Timer Interrupt Pending",
            9: "SEIP - Supervisor External Interrupt Pending",
            13: "LCOFIP - Local Core Overflow Interrupt Pending"
        })

    def handle_exception(self):
        print(f"Exception: Illegal write to WPRI bits in {self.name}")

    def check_invalid_write(self, new_binary_string):
        """Kiểm tra nếu ghi sai vào các bit WPRI."""
        for bit in self.WPRI_BITS:
            old_bit = self.value[31 - bit]
            new_bit = new_binary_string[31 - bit]
            if old_bit != new_bit:
                self.handle_exception()
                break

    def write(self, binary_string):
        if len(binary_string) != 32 or not all(c in "01" for c in binary_string):
            raise ValueError("Input must be a 32-bit binary string.")
        self.check_invalid_write(binary_string)
        self.value = binary_string
class SCOUNTEREN(CSR32):
    def __init__(self):
        super().__init__("scounteren")
        self.set_important_bits({
            0: "CY - Cho phép U-mode đọc thanh ghi cycle",
            1: "TM - Cho phép U-mode đọc thanh ghi time",
            2: "IR - Cho phép U-mode đọc thanh ghi instret"
        })
class SSCRATCH(CSR32):
    def __init__(self):
        super().__init__("sscratch")
class SEPC(CSR32):
    def __init__(self):
        super().__init__("sepc")

    def save_pc(self, pc_value):
        """ Lưu giá trị PC hiện tại vào SEPC mà không thay đổi. """
        binary_pc = f"{pc_value:032b}"  # Chuyển PC thành chuỗi nhị phân 32-bit
        self.write(binary_pc)

    def restore_pc(self):
        """ Khôi phục giá trị PC từ SEPC. """
        return int(self.read(), 2)  # Chuyển từ nhị phân về số nguyên
class SCause(CSR32):
    def __init__(self):
        super().__init__("scause")
        self.cause_mapping = {
            0: "Instruction address misaligned",
            1: "Instruction access fault",
            2: "Illegal instruction",
            3: "Breakpoint",
            4: "Load address misaligned",
            5: "Load access fault",
            6: "Store/AMO address misaligned",
            7: "Store/AMO access fault",
            8: "Environment call from U-mode",
            9: "Environment call from S-mode",
            12: "Instruction page fault",
            13: "Load page fault",
            15: "Store/AMO page fault"
        }
    
    def set_cause(self, cause, interrupt=False):
        """ Thiết lập nguyên nhân của trap với mã cause và loại trap (interrupt hoặc exception). """
        if not (0 <= cause < (1 << 31)):
            raise ValueError("Cause code phải nằm trong khoảng hợp lệ 0-2^31-1.")
        
        bit_list = list("0" * 32)
        
        # Nếu là interrupt, bật bit 31
        if interrupt:
            bit_list[0] = '1'  # Bit 31 là MSB

        # Mã cause được đặt từ bit 0-30
        binary_cause = f"{cause:030b}"
        bit_list[2:] = list(binary_cause)  # Điền vào từ bit 0-30
        
        self.value = "".join(bit_list)

    def set_cause_by_description(self, description, interrupt=False):
        """ Đặt giá trị scause dựa trên mô tả của nguyên nhân. """
        for cause_code, desc in self.cause_mapping.items():
            if desc.lower() == description.lower():  # So sánh không phân biệt hoa thường
                self.set_cause(cause_code, interrupt)
                return
        raise ValueError(f"Không tìm thấy nguyên nhân '{description}' trong scause")

    def get_cause_info(self):
        """ Đọc giá trị hiện tại của scause và diễn giải nó. """
        binary_value = self.value
        interrupt = binary_value[0] == '1'  # Bit 31
        cause_code = int(binary_value[2:], 2)  # Bits 0-30
        
        cause_desc = self.cause_mapping.get(cause_code, "Unknown cause")
        trap_type = "Interrupt" if interrupt else "Exception"
        
        return f"{trap_type}: {cause_desc} (Cause Code {cause_code})"
    def get_cause_code(self):
        """Lấy mã cause từ thanh ghi scause."""
        binary_value = self.value
        return int(binary_value[2:], 2)  # Bits 0-30
class STval(CSR32):
    def __init__(self):
        super().__init__("stval")
class SENVCFG(CSR32):
    # Các bit hợp lệ được phép ghi
    VALID_BITS = {0, 4, 6, 7}

    def __init__(self):
        super().__init__("senvcfg")
        self.set_important_bits({
            0: "FIOM - Fence của I/O ngụ ý Fence của bộ nhớ",
            4: "CBIE - Điều khiển bỏ qua bộ nhớ cache",
            6: "CBCFE - Điều khiển bỏ qua cache cho fence",
            7: "CBZE - Điều khiển bỏ qua cache cho zeroing",
        })

    def handle_exception(self):
        print(f"Exception: Illegal write to WPRI bits in {self.name}")

    def check_invalid_write(self, new_binary_string):
        """Kiểm tra nếu ghi sai vào các bit WPRI."""
        for bit in range(32):
            if bit not in self.VALID_BITS:
                old_bit = self.value[31 - bit]
                new_bit = new_binary_string[31 - bit]
                if old_bit != new_bit:
                    self.handle_exception()
                    break

    def write(self, binary_string):
        if len(binary_string) != 32 or not all(c in "01" for c in binary_string):
            raise ValueError("Input must be a 32-bit binary string.")
        self.check_invalid_write(binary_string)
        self.value = binary_string
class SATP(CSR32):
    def __init__(self):
        super().__init__("satp")
        self.set_important_bits({
            31: "Mode Bit - Determines address translation mode"
        })

class DCSR(CSR32):
    def __init__(self):
        super().__init__("dcsr")
        self.set_important_bits({
            DCSR_PRV0_BIT:         "prv[0] - Privilege level bit 0",
            DCSR_PRV1_BIT:         "prv[1] - Privilege level bit 1",
            DCSR_STEP_BIT:         "step - Enable single-step",
            DCSR_NMIP_BIT:         "nmip - Indicates NMI caused entry",
            DCSR_MPRVEN_BIT:       "mprven - Use mstatus.mprv",
            DCSR_V_BIT:            "v - (reserved or vector extension)",
            DCSR_CAUSE0_BIT:       "cause[0] - Debug cause bit 0",
            DCSR_CAUSE1_BIT:       "cause[1] - Debug cause bit 1",
            DCSR_CAUSE2_BIT:       "cause[2] - Debug cause bit 2",
            DCSR_STOPTIME_BIT:     "stoptime - Stop timers while in debug",
            DCSR_STOPCOUNT_BIT:    "stopcount - Stop counters while in debug",
            DCSR_STEP_IE_BIT:      "stepie - Re-enable interrupts after step",
            DCSR_EBREAKU_BIT:      "ebreaku - Enter Debug on ebreak from U-mode",
            DCSR_EBREAKS_BIT:      "ebreaks - Enter Debug on ebreak from S-mode",
            DCSR_EBREAKM_BIT:      "ebreakm - Enter Debug on ebreak from M-mode",
            DCSR_EBREAKVS_BIT:     "ebreakvs - Enter Debug on ebreak from VS-mode (H-ext)",
            DCSR_EBREAKVU_BIT:     "ebreakvu - Enter Debug on ebreak from VU-mode (H-ext)",
            DCSR_PELP_BIT:         "pelp - Platform-defined bit",
            DCSR_CETRIG_BIT:       "cetrig - Platform-defined bit",
            DCSR_EXTCAUSE0_BIT:    "extcause[0] - External cause bit 0",
            DCSR_EXTCAUSE1_BIT:    "extcause[1] - External cause bit 1",
            DCSR_EXTCAUSE2_BIT:    "extcause[2] - External cause bit 2",
            DCSR_DEBUGVER0_BIT:    "debugver[0] - Debug spec version bit 0",
            DCSR_DEBUGVER1_BIT:    "debugver[1] - Debug spec version bit 1",
            DCSR_DEBUGVER2_BIT:    "debugver[2] - Debug spec version bit 2",
            DCSR_DEBUGVER3_BIT:    "debugver[3] - Debug spec version bit 3"
        })


    def get_privilege_mode(self):
        prv = int(self.value[29:31], 2)
        return ["User", "Supervisor", "Hypervisor", "Machine"][prv]

    def get_debug_cause(self):
        cause_bits = self.value[25:27]
        cause_dict = {
            "00": "Ebreak",
            "01": "Trigger",
            "10": "Single-step",
            "11": "Reset-haltreq"
        }
        return cause_dict.get(cause_bits, "Unknown")
class DPC(CSR32):
    def __init__(self):
        super().__init__("dpc")

    def save_pc(self, pc_value):
        binary_pc = f"{pc_value:032b}"
        self.write(binary_pc)

    def restore_pc(self):
        return int(self.read(), 2)
class DScratch0(CSR32):
    def __init__(self):
        super().__init__("dscratch0")
class DScratch1(CSR32):
    def __init__(self):
        super().__init__("dscratch1")

sstatus = SStatus()
stvec = STVec()
stvec.write(handler_base_addr)
sip = SIP()
sie = SIE()
scounteren = SCOUNTEREN()
sscratch = SSCRATCH()
sepc = SEPC()
scause = SCause()
stval = STval()
senvcfg = SENVCFG()
satp = SATP()

dcsr = DCSR()
dpc = DPC()
dscratch0 = DScratch0()
dscratch1 = DScratch1()
csrs = {
    "sstatus": sstatus,
    "stvec": stvec,
    "sip": sip,
    "sie": sie,
    "scounteren": scounteren,
    "sscratch": sscratch,
    "sepc": sepc,
    "scause": scause,
    "stval": stval,
    "senvcfg": senvcfg,
    "satp": satp,
}



# Execute R-type instructions
def executeR(opcode, rd, rs1, rs2, func3, func7, inst):
    rd_dec = int(rd, 2)
    rs1_dec = int(rs1, 2)
    rs2_dec = int(rs2, 2)
    mnemonic = "unknown"

    if opcode == "0110011":  # R-type instructions
        if func3 == "000" and func7 == "0000000":  # ADD
            registerFiles[str(rd_dec)] = registerFiles[str(rs1_dec)] + registerFiles[str(rs2_dec)]
            mnemonic = "add"
        elif func3 == "000" and func7 == "0100000":  # SUB
            registerFiles[str(rd_dec)] = registerFiles[str(rs1_dec)] - registerFiles[str(rs2_dec)]
            mnemonic = "sub"
        elif func3 == "001":  # SLL (Shift Left Logical)
            shift_amount = registerFiles[str(rs2_dec)] & 0b11111
            registerFiles[str(rd_dec)] = (registerFiles[str(rs1_dec)] << shift_amount) & 0xFFFFFFFF
            mnemonic = "sll"
        elif func3 == "010":  # SLT
            registerFiles[str(rd_dec)] = 1 if registerFiles[str(rs1_dec)] < registerFiles[str(rs2_dec)] else 0
            mnemonic = "slt"
        elif func3 == "011":  # SLTU
            registerFiles[str(rd_dec)] = 1 if (registerFiles[str(rs1_dec)] & 0xFFFFFFFF) < (registerFiles[str(rs2_dec)] & 0xFFFFFFFF) else 0
            mnemonic = "sltu"
        elif func3 == "100":  # XOR
            registerFiles[str(rd_dec)] = registerFiles[str(rs1_dec)] ^ registerFiles[str(rs2_dec)]
            mnemonic = "xor"
        elif func3 == "101" and func7 == "0000000":  # SRL
            shift_amount = registerFiles[str(rs2_dec)] & 0b11111
            registerFiles[str(rd_dec)] = (registerFiles[str(rs1_dec)] >> shift_amount) & 0xFFFFFFFF
            mnemonic = "srl"
        elif func3 == "101" and func7 == "0100000":  # SRA
            shift_amount = registerFiles[str(rs2_dec)] & 0b11111
            registerFiles[str(rd_dec)] = registerFiles[str(rs1_dec)] >> shift_amount
            mnemonic = "sra"
        elif func3 == "110":  # OR
            registerFiles[str(rd_dec)] = registerFiles[str(rs1_dec)] | registerFiles[str(rs2_dec)]
            mnemonic = "or"
        elif func3 == "111":  # AND
            registerFiles[str(rd_dec)] = registerFiles[str(rs1_dec)] & registerFiles[str(rs2_dec)]
            mnemonic = "and"

    # Trả về chuỗi lệnh disassembled
    return f"{mnemonic} x{rd_dec}, x{rs1_dec}, x{rs2_dec}"

def executeI(opcode, rd, rs1, imm2, func3, inst):
    global pc
    rd_dec = int(rd, 2)
    rs1_dec = int(rs1, 2)
    imm=imm2[0:12]
    mnemonic = "unknown"
    if opcode == "0010011":  # I-type instructions (Immediate Arithmetic)
        rd = str(int(rd,2))
        rs1 = str(int(rs1,2))
        if func3 == "000":  # addi
            registerFiles[rd] = registerFiles[rs1] + int(imm, 2)
            mnemonic = "addi"
        elif func3 == "111":  # andi
            registerFiles[rd] = registerFiles[str(rs1)] & imm
            mnemonic = "andi"
        elif func3 == "100":  # xori
            registerFiles[rd] = registerFiles[str(rs1)] ^ int(imm,2)
            mnemonic = "xori"
        elif func3 == "010":  # slti
            registerFiles[rd] = 1 if registerFiles[str(rs1)] < imm else 0
            mnemonic = "slti"
        elif func3 == "011":  # sltiu
            registerFiles[rd] = 1 if (registerFiles[str(rs1)] & 0xFFFFFFFF) < (imm & 0xFFFFFFFF) else 0
            mnemonic = "sltiu"
        elif func3 == "001":  # slli
            shift_amount = int(imm,2) & 0b11111  # Lấy 5 bit thấp nhất của immediate
            registerFiles[rd] = registerFiles[str(rs1)] << shift_amount
            registerFiles[rd] &= 0xFFFFFFFF  # Đảm bảo kết quả nằm trong 32-bit
            mnemonic = "slli"
        elif func3 == "101":  # srli/srai
            shift_amount = imm & 0b11111  # Lấy 5 bit thấp nhất của immediate
            if imm >> 5 == 0:  # Kiểm tra xem là SRL hay SRA
                registerFiles[rd] = (registerFiles[str(rs1)] >> shift_amount) & 0xFFFFFFFF
            else:
                registerFiles[rd] = registerFiles[str(rs1)] >> shift_amount
            mnemonic = "srli"
        elif func3 == "110":  # ori
            registerFiles[rd] = registerFiles[str(rs1)] | imm
            mnemonic = "ori"
        return f"{mnemonic} x{rd_dec}, x{rs1_dec}, {int(imm,2)}"
    elif opcode == "0000011":  # I-type Load instructions
        imm=int(imm,2)
        rd = str(int(rd,2))
        rs1 = str(int(rs1,2))
        address = registerFiles[str(rs1)] + imm
        if (address % 4!=0):
            scause.set_cause_by_description("Load address misaligned")
            handle_exception(format(address, '032b'))
            pc-=4
        if (address >= 805306368):
            scause.set_cause_by_description("Load access fault")
            handle_exception(format(address, '032b'))
            pc-=4
        if func3 == "000":  # lb
            value = dataMemory.get(address, 0)  # Lấy giá trị tại địa chỉ bộ nhớ
            registerFiles[rd] = (value & 0xFF)  # Chỉ lấy 1 byte và mở rộng dấu
            if registerFiles[rd] & 0x80:  # Kiểm tra bit dấu
                registerFiles[rd] |= 0xFFFFFF00  # Mở rộng dấu
            mnemonic = "lb"
        elif func3 == "001":  # lh
            value = dataMemory.get(address, 0)  # Lấy giá trị tại địa chỉ bộ nhớ
            registerFiles[rd] = (value & 0xFFFF)  # Chỉ lấy 2 byte và mở rộng dấu
            if registerFiles[rd] & 0x8000:  # Kiểm tra bit dấu
                registerFiles[rd] |= 0xFFFF0000  # Mở rộng dấu
            mnemonic = "lh"
        elif func3 == "010":  # lw
            registerFiles[rd] = dataMemory.get(address, 0)  # Tải 4 byte từ bộ nhớ
            mnemonic = "lw"
        elif func3 == "011":  # ld
            registerFiles[rd] = dataMemory.get(address, 0)  # Tải 8 byte từ bộ nhớ
            mnemonic = "ld"
        elif func3 == "100":  # lbu
            value = dataMemory.get(address, 0)  # Lấy giá trị tại địa chỉ bộ nhớ
            registerFiles[rd] = value & 0xFF  # Chỉ lấy 1 byte và mở rộng không dấu
            mnemonic = "lbu"
        elif func3 == "101":  # lhu
            value = dataMemory.get(address, 0)  # Lấy giá trị tại địa chỉ bộ nhớ
            registerFiles[rd] = value & 0xFFFF  # Chỉ lấy 2 byte và mở rộng không dấu
            mnemonic = "lhu"
        return f"{mnemonic} x{rd_dec}, {int(imm)}(x{rs1_dec})"
def executeS(opcode, rd, rs1, rs2, imm2, func3, func7, inst):
    global pc
    rd_dec = int(rd, 2)
    rs1_dec = int(rs1, 2)
    rs2_dec = int(rs2, 2)
    mnemonic = "unknown"
    if opcode == "0100011":  # S-type store instructions
        rd = str(int(rd,2))
        rs1 = str(int(rs1,2))
        rs2 = str(int(rs2,2))
        imm = (int(func7, 2) << 5) | int(rd)  # Ghép func7 và rd thành immediate 12 bit
        
        address = registerFiles[str(rs1)] + imm  # Tính toán địa chỉ bộ nhớ bằng cách cộng rs1 và immediate
        if (address % 4!=0):
            scause.set_cause_by_description("Store/AMO address misaligned")
            handle_exception(format(address, '032b'))
            pc-=4
        if (address >= 805306368):
            scause.set_cause_by_description("Store/AMO access fault")
            handle_exception(format(address, '032b'))
            pc-=4
        if func3 == "000":  # sb (Store Byte)
            dataMemory[address] = registerFiles[rs2] & 0xFF  # Lưu 1 byte vào bộ nhớ
            mnemonic = "sb"
        elif func3 == "001":  # sh (Store Halfword)
            dataMemory[address] = registerFiles[rs2] & 0xFFFF  # Lưu 2 byte vào bộ nhớ
            mnemonic = "sh"
        elif func3 == "010":  # sw (Store Word)
            dataMemory[address] = registerFiles[rs2] & 0xFFFFFFFF  # Lưu 4 byte vào bộ nhớ
            mnemonic = "sw"
        elif func3 == "011":  # sd (Store Doubleword) [Chỉ có trên RISC-V 64-bit]
            dataMemory[address] = registerFiles[rs2]  # Lưu 8 byte vào bộ nhớ
            mnemonic = "sd"
        return f"{mnemonic} x{rs2_dec}, {int(imm)}(x{rs1_dec})"
def executeB(opcode, rs1, rs2, rd, func3, func7, imm2, inst):
    global pc
    rd_dec = int(rd, 2)
    rs1_dec = int(rs1, 2)
    rs2_dec = int(rs2, 2)
    mnemonic = "unknown"
    if opcode == "1100011":  # B-type branch instructions
        rs1 = str(int(rs1, 2))
        rs2 = str(int(rs2, 2))
        imm_12 = imm2[0]
        imm_10_5= imm2[1:7]
        imm_4_1 = rd[0:4]
        imm_11 = rd[4]
        imm_binary = imm_12 + imm_11 + imm_10_5 + imm_4_1 + '0'
        imm = int(imm_binary, 2)
        if imm & (1 << 12):  # Nếu bit dấu (bit 20) là 1
            imm -= (1 << 13)  # Chuyển sang số âm
            imm -=4
        # Kiểm tra điều kiện nhảy dựa trên func3
        if func3 == "000":  # BEQ (Branch if Equal)
            if registerFiles[str(rs1)] == registerFiles[rs2]:
                pc += imm
            mnemonic = "beq"
        elif func3 == "001":  # BNE (Branch if Not Equal)
            if registerFiles[str(rs1)] != registerFiles[rs2]:
                pc += imm
            mnemonic = "bne"
        elif func3 == "100":  # BLT (Branch if Less Than)
            if registerFiles[str(rs1)] < registerFiles[rs2]:
                pc += imm
            mnemonic = "blt"
        elif func3 == "101":  # BGE (Branch if Greater or Equal)
            if registerFiles[str(rs1)] >= registerFiles[rs2]:
                pc += imm
            mnemonic = "bge"
        elif func3 == "110":  # BLTU (Branch if Less Than Unsigned)
            if (registerFiles[str(rs1)] & 0xFFFFFFFF) < (registerFiles[rs2] & 0xFFFFFFFF):
                pc += imm
            mnemonic = "bltu"
        elif func3 == "111":  # BGEU (Branch if Greater or Equal Unsigned)
            if (registerFiles[str(rs1)] & 0xFFFFFFFF) >= (registerFiles[rs2] & 0xFFFFFFFF):
                pc += imm
            mnemonic = "bgeu"
        return f"{mnemonic} x{rs1_dec}, x{rs2_dec}, {int(imm)}"
def executeU(opcode, rd, imm, inst):
    mnemonic = "lui"
    rd = str(int(rd,2))
    imm = int(imm, 2)  # Chuyển đổi immediate từ nhị phân sang số nguyên
    if opcode == "0110111":  # lui (Load Upper Immediate)
        registerFiles[rd] = imm << 12  # Shift immediate trái 12 bit (tương đương với nhân 2^12)
    return f"{mnemonic} x{rd}, {int(imm)}"
def executeJ(opcode, rd, imm2, inst):
    global pc
    mnemonic = "jal"
    # Lấy các trường của imm
    imm_20 = imm2[0]  # Bit imm[20]
    imm_10_1 = imm2[1:11]  # Bits imm[19:12]
    imm_11 = imm2[11]  # Bit imm[11]
    imm_19_12 = imm2[12:20]  # Bits imm[10:1]

    # Ghép các trường lại theo thứ tự imm[20] | imm[19:12] | imm[11] | imm[10:1] | 0
    imm_binary = imm_20 + imm_19_12 + imm_11 + imm_10_1 + '0'

    # Chuyển từ nhị phân sang số nguyên có dấu
    imm = int(imm_binary, 2)
    jump_address = pc + imm * 800
    if (jump_address >= 805306368):
        scause.set_cause_by_description("Instruction access fault")
        handle_exception(format(jump_address, '032b'))
        return
    if imm & (1 << 20):  # Nếu bit dấu (bit 20) là 1
        imm -= (1 << 21)  # Chuyển sang số âm

    if opcode == "1101111":  # JAL (Jump and Link)
        rd = str(int(rd, 2))
        
        # Tính giá trị immediate (imm) đã được decode thành số nguyên có dấu
        jump_address2 = pc + imm
        if (jump_address2 % 4 !=0):
            scause.set_cause_by_description("Instruction address misaligned")
            handle_exception(format(jump_address, '032b'))
            return
        # Cập nhật PC đến địa chỉ nhảy
        pc = jump_address2
        # Lưu giá trị của PC hiện tại + 4 (địa chỉ lệnh tiếp theo) vào rd
        registerFiles[rd] = pc + 4
        return f"{mnemonic} x{rd}, {int(imm)}"
def executeSupervisor(opcode, rd, rs1, rs2, imm2, func3, func7, inst):
    global pc
    rd_dec = int(rd, 2)
    rs1_dec = int(rs1, 2)
    rs2_dec = int(rs2, 2)
    mnemonic = "unknown"
    imm = imm2[0:12]
    imm3 = imm2[0:7]
    rs1 = int(str(rs1),2)
    rd = str(int(rd, 2))
    if opcode == "1110011":  # Lệnh đặc quyền (Privileged Instructions)
        if imm3 == "0001001":  # sfence.vma
            handle_sfence_vma()
            mnemonic = "sfence.vma"
        if func3 == "001": #csrrw
            mnemonic = "csrrw"
            if imm == "000100000000":
                registerFiles[rd] = int(sstatus.read(),2)
                sstatus.write(format(registerFiles[str(rs1)], '032b'))
                pc+=4
                return f"{mnemonic} x{rd_dec}, sstatus, x{rs1_dec}"
            elif imm == "000100000101":
                registerFiles[rd] = int(stvec.read(),2)
                stvec.write(format(registerFiles[str(rs1)], '032b'))
                pc+=4
                return f"{mnemonic} x{rd_dec}, stvec, x{rs1_dec}"
            elif imm == "000101000100":
                registerFiles[rd] = int(sip.read(),2)
                sip.write(format(registerFiles[str(rs1)], '032b'))
                pc+=4
                return f"{mnemonic} x{rd_dec}, sip, x{rs1_dec}"
            elif imm == "000100000100":
                registerFiles[rd] = int(sie.read(),2)
                sie.write(format(registerFiles[str(rs1)], '032b'))
                pc+=4
                return f"{mnemonic} x{rd_dec}, sie, x{rs1_dec}"
            elif imm == "000100000110":
                registerFiles[rd] = int(scounteren.read(),2)
                scounteren.write(format(registerFiles[str(rs1)], '032b'))
                pc+=4
                return f"{mnemonic} x{rd_dec}, scounteren, x{rs1_dec}"
            elif imm == "000101000000":
                registerFiles[rd] = int(sscratch.read(),2)
                sscratch.write(format(registerFiles[str(rs1)], '032b'))
                pc+=4
                return f"{mnemonic} x{rd_dec}, sscratch, x{rs1_dec}"
            elif imm == "000101000001":
                registerFiles[rd] = int(sepc.read(),2)
                sepc.write(format(registerFiles[str(rs1)], '032b'))
                pc+=4
                return f"{mnemonic} x{rd_dec}, sepc, x{rs1_dec}"
            elif imm == "000101000010":
                registerFiles[rd] = int(scause.read(),2)
                scause.write(format(registerFiles[str(rs1)], '032b'))
                pc+=4
                return f"{mnemonic} x{rd_dec}, scause, x{rs1_dec}"
            elif imm == "000101000011":
                registerFiles[rd] = int(stval.read(),2)
                stval.write(format(registerFiles[str(rs1)], '032b'))
                pc+=4
                return f"{mnemonic} x{rd_dec}, stval, x{rs1_dec}"
            elif imm == "000100001010":
                registerFiles[rd] = int(senvcfg.read(),2)
                senvcfg.write(format(registerFiles[str(rs1)], '032b'))
                pc+=4
                return f"{mnemonic} x{rd_dec}, senvcfg, x{rs1_dec}"
            elif imm == "000110000000":
                registerFiles[rd] = int(satp.read(),2)
                satp.write(format(registerFiles[str(rs1)], '032b'))
                pc+=4
                return f"{mnemonic} x{rd_dec}, satp, x{rs1_dec}"
            
        if func3 == "000":
            if imm == "000000000000":  # ecall
                mnemonic = "ecall"
                handle_ecall()
                return f"{mnemonic}"
            elif imm == "000000000001":  # ebreak
                mnemonic = "ebreak"
                handle_ebreak()
                return f"{mnemonic}"
            elif imm == "001100000010":  # mret
                mnemonic = "mret"
                handle_mret()
                return f"{mnemonic}"
            elif imm == "000100000010":  # sret
                mnemonic = "sret"
                global SUPERVISOR_MODE
                SUPERVISOR_MODE = not SUPERVISOR_MODE
                pc+=4
                return f"{mnemonic}"
            elif imm == "011100000010":  # mnret
                mnemonic = "mret"
                handle_mnret()
                return f"{mnemonic}"
            elif imm == "000100000101":  # wfi
                mnemonic = "wfi"
                handle_wfi()
                return f"{mnemonic}"

def handle_exception(parameter):
    global pc

    # Lấy mã lỗi và in mô tả lỗi
    cause_code = scause.get_cause_code()
    cause_info = scause.get_cause_info()
    print(f"Exception xảy ra: {cause_info}")

    # Lưu trạng thái PC trước trap
    sepc.save_pc(pc)
    sstatus.activate_bit(SSTATUS_SPIE_BIT)

    # Ghi giá trị vào stval tùy theo loại lỗi
    if cause_code in [Illegal_instruction]:  # Illegal instruction
        if parameter == pc:
            parameter = format(pc, '032b')
        stval.write(parameter)
    elif cause_code in [Instruction_address_misaligned, Instruction_access_fault, Instruction_page_fault]:  # Instruction address misaligned/fault/page fault
        stval.write(parameter)
    elif cause_code in [Load_address_misaligned,Load_access_fault, Load_page_fault, StoreAMO_address_misaligned, StoreAMO_access_fault, StoreAMO_page_fault]:  # Load/Store faults
        stval.write(parameter)
    elif cause_code == Breakpoint:  # Breakpoint (ebreak)
        stval.write(format(pc, '032b'))

        # Xác định privilege hiện tại để kiểm tra bit tương ứng
        priv = sstatus.value[29:31]  # 2-bit privilege level (00=U, 01=S, 11=M)
        priv_mode = int(priv, 2)

        if  (priv_mode == 0 and dcsr.value[31 - DCSR_EBREAKU_BIT] == '1') or \
            (priv_mode == 1 and dcsr.value[31 - DCSR_EBREAKS_BIT] == '1') or \
            (priv_mode == 3 and dcsr.value[31 - DCSR_EBREAKM_BIT] == '1'):
            # Vào Debug Mode
            handle_breakpoint()
            return  # Không thực hiện tiếp handler trap thông thường

    else:
        stval.write(0)

    # Tính địa chỉ handler từ stvec
    pc = stvec.set_pc(cause_code)

    # Lưu các thanh ghi vào stack
    save_registers_to_stack(registerFiles, stack)

    # Handler ánh xạ theo cause_code thay vì mô tả
    handlers = {
        Instruction_address_misaligned: handle_instruction_address_misaligned,
        Instruction_access_fault: handle_instruction_access_fault,
        Illegal_instruction: handle_illegal_instruction,
        Breakpoint: handle_breakpoint,
        Load_address_misaligned: handle_misaligned_access,
        Load_access_fault: handle_access_fault,
        StoreAMO_address_misaligned: handle_misaligned_access,
        StoreAMO_access_fault: handle_access_fault,
        Environment_call_from_Umode: handle_ecall_from_u_mode,
        Environment_call_from_Smode: handle_ecall_from_s_mode,
        Instruction_page_fault: handle_page_fault,
        Load_page_fault: handle_page_fault,
        StoreAMO_page_fault: handle_page_fault
    }

    # Gọi hàm xử lý tương ứng, fallback nếu không có
    handler_func = handlers.get(cause_code, handle_unknown_exception)
    handler_func()

    # Phục hồi trạng thái
    restore_registers_from_stack(registerFiles, stack)
    handle_sret()
    pc+=4

def save_registers_to_stack(registerFiles, stack):
    """
    Lưu các thanh ghi từ registerFiles vào stack (list).
    """
    for i in range(32):
        reg_name = str(i)
        stack.append(registerFiles[reg_name])  # push vào stack
def restore_registers_from_stack(registerFiles, stack):
    """
    Phục hồi các thanh ghi từ stack vào registerFiles.
    """
    for i in reversed(range(32)):
        reg_name = str(i)
        registerFiles[reg_name] = stack.pop()# pop từ stack


def handle_instruction_address_misaligned():
    print("Lỗi: Instruction address misaligned")
def handle_instruction_access_fault():
    print("Lỗi: Instruction access fault")
def handle_illegal_instruction():
    print("Lỗi: Illegal instruction")
def handle_breakpoint():
    global pc
    global debug_mode
    
    print("EBREAK detected: entering debug mode")
    debug_mode = True
    dpc.save_pc(pc)

    # Set dcsr.cause = 0 (Ebreak)
    dcsr.write(dcsr.value[:25] + "00" + dcsr.value[27:])  # Bits 6:5 = 00

    # Debug trap entry point có thể mô phỏng tại đây nếu cần
    print("Hart is halted. Waiting for debug resume...")

def handle_misaligned_access():
    print("Lỗi: Misaligned access (load/store)")
def handle_access_fault():
    print("Lỗi: Access fault (load/store)")
def handle_ecall_from_u_mode():
    print("Exception xảy ra: Exception: ECALL from U-mode (Cause Code 8)")
    # Có thể gọi lại handle_ecall() nếu muốn
def handle_ecall_from_s_mode():
    print("Exception xảy ra: Exception: ECALL from S-mode (Cause Code 9)")
def handle_page_fault():
    print("Lỗi: Page fault")
def handle_unknown_exception():
    print("Lỗi không xác định")


def handle_ecall():
    global SUPERVISOR_MODE
    if SUPERVISOR_MODE == True:
            handle_ecall_from_s_mode()
    else: handle_ecall_from_u_mode()
    
    a7 = registerFiles["17"]  # Mã syscall
    a0 = registerFiles["10"]  # Tham số chính của syscall
    a2 = registerFiles["12"]  # Tham số phụ (nếu có)

    ecall_descriptions = {
        ECALL["PRINT_INT"]: "Print integer (a0 = số cần in)",
        ECALL["PRINT_FLOAT"]: "Print float (fa0 = số cần in)",
        ECALL["PRINT_DOUBLE"]: "Print double (fa0 = số cần in)",
        ECALL["PRINT_STRING"]: "Print string (a0 = địa chỉ chuỗi)",
        ECALL["READ_INT"]: "Read integer (a0 = kết quả nhập)",
        ECALL["READ_FLOAT"]: "Read float (fa0 = kết quả nhập)",
        ECALL["READ_DOUBLE"]: "Read double (fa0 = kết quả nhập)",
        ECALL["READ_STRING"]: "Read string (a0 = buffer, a1 = độ dài)",
        ECALL["SBRK"]: "Memory allocation (sbrk, a0 = kích thước)",
        ECALL["EXIT"]: "Exit program (a0 = mã thoát)",
        ECALL["PRINT_CHAR"]: "Print character (a0 = ký tự ASCII)",
        ECALL["READ_CHAR"]: "Read character (a0 = ký tự nhập)",
        ECALL["OPEN_FILE"]: "Open file (a0 = filename, a1 = mode)",
        ECALL["READ_FILE"]: "Read file (a0 = fd, a1 = buffer, a2 = bytes)",
        ECALL["WRITE_FILE"]: "Write file (a0 = fd, a1 = buffer, a2 = bytes)",
        ECALL["CLOSE_FILE"]: "Close file (a0 = file descriptor)"
    }
    global pc
    if a7 in ecall_descriptions:
        sepc.save_pc(pc)
        if SUPERVISOR_MODE == True:
            scause.set_cause_by_description("Environment call from S-mode")
        else: scause.set_cause_by_description("Environment call from U-mode")
        sstatus.activate_bit(SSTATUS_SPIE_BIT)
        pc = stvec.set_pc(int(scause.get_cause_code()))
        handler_ecall(a7, a0, a2)
        handle_sret()
        pc += 4

def handler_ecall(ecall_type, ecall_param_1, ecall_param_2):
    if ecall_type == ECALL["READ_INT"]:
        registerFiles["10"] = int(input())
        IO.update({"input": registerFiles["10"]})
    elif ecall_type == ECALL["PRINT_INT"]:
        print(registerFiles["10"])
        IO.update({"output": registerFiles["10"]})
    elif ecall_type == ECALL["READ_CHAR"]:
        registerFiles["10"] = ord(input()[0])
        IO.update({"input": registerFiles["10"]})
    elif ecall_type == ECALL["PRINT_CHAR"]:
        print(chr(registerFiles["10"]))
        IO.update({"output": registerFiles["10"]})
    elif ecall_type == ECALL["EXIT"]:
        exit()
def handle_ebreak():
    global pc
    print("Executing EBREAK")
    scause.set_cause_by_description("Breakpoint")
    handle_exception(pc)
def handle_mret():
    print("Executing MRET")
def handle_sret():
    global pc
    pc = sepc.restore_pc() # Lấy giá trị PC đúng từ SEPC
def handle_mnret():
    print("Executing MNRET")
def handle_wfi():
    print("Executing WFI")
def handle_sfence_vma():
    print("Executing SFENCE.VMA")

# Decode instruction
def instDecoder(inst):
    # Parse instruction fields
    opcode = inst[25:32]  # Opcode (bits 25-31)
    func3 = inst[17:20]   # func3 (bits 17-19)
    func7 = inst[0:7]     # func7 (bits 0-6)
    rs1 = inst[12:17]   # rs1 (bits 12-16)
    rs2 = inst[7:12]    # rs2 (bits 7-11)
    rd = inst[20:25]    # rd (bits 20-24)
    imm = inst[0:20]  # Immediate value
    if opcode == "0110011":
        format = "R"
    elif opcode == "0000011" or opcode == "0010011":
        format = "I"
    elif opcode == "0100011":
        format = "S"
    elif opcode == "1100011":
        format = "B"
    elif opcode == "0110111":
        format = "U"
    elif opcode == "1110011":
        format = "Supervisor"
    elif opcode == "1101111":
        format = "J"
    else:
        format = "Exception"
    return format, opcode, func3, func7, rd, rs1, rs2, imm

def run_normal_instruction(format, opcode, func3, func7, rd, rs1, rs2, imm, inst):
    global pc
    if format == "R":
        executeR(opcode, rd, rs1, rs2, func3, func7, inst)
        pc += 4
    elif format == "I":
        executeI(opcode, rd, rs1, imm, func3, inst)
        pc += 4
    elif format == "S":
        executeS(opcode, rd, rs1, rs2, imm, func3, func7, inst)
        pc += 4
    elif format == "B":
        executeB(opcode, rs1, rs2, rd, func3, func7, imm, inst)
        pc += 4
    elif format == "U":
        executeU(opcode, rd, imm, inst)
        pc += 4
    elif format == "Supervisor":
        executeSupervisor(opcode, rd, rs1, rs2, imm, func3, func7, inst)
    elif format == "J":
        old_pc = pc
        executeJ(opcode, rd, imm, inst)
        if pc == old_pc:
            pc += 4
    else:
        scause.set_cause_by_description("Illegal instruction")
        handle_exception(inst)

def run_debug_loop(instructions):
    global pc, debug_mode
    while True:
        debug_command = input("please enter instruction: ").strip()

        if debug_command.startswith("r "):
            try:
                run_count = int(debug_command.split()[1])
                for _ in range(run_count):
                    inst = instructions[pc // 4].strip()
                    if inst[0] == 'E':
                        scause.set_cause_by_description("Illegal instruction")
                        handle_exception(pc)
                        break

                    format, opcode, func3, func7, rd, rs1, rs2, imm = instDecoder(inst)
                    RISCV_inst = execute_instruction(format, opcode, func3, func7, rd, rs1, rs2, imm, inst)
                    print(f"0x{pc:08x}  {RISCV_inst} {int(inst, 2):08x}")
            except:
                print("Invalid format. Use: r N (e.g., r 5)")

        elif debug_command == "r":
            debug_mode = False
            break

        elif debug_command == "exit":
            exit()

        elif debug_command.startswith("reg x"):
            try:
                reg_num = int(debug_command[5:])
                if 0 <= reg_num <= 31:
                    print(f"x{reg_num} = 0x{registerFiles[str(reg_num)]:08x}")
                else:
                    print("Register number must be between x0 and x31.")
            except ValueError:
                print("Invalid register number format.")

        elif debug_command == "reg all":
            print("==== General Purpose Registers (x0 - x31) ====")
            for i in range(32):
                print(f"x{i:2} = 0x{registerFiles[str(i)]:08x}", end='\t')
                if (i + 1) % 4 == 0:
                    print()

        elif debug_command == "pc":
            print(f"PC = 0x{pc:08x}")

        elif debug_command == "csr":
            print("==== Control and Status Registers (CSR) ====")
            for name, reg_obj in csrs.items():
                print(f"{name:10} = 0x{int(reg_obj.read()):08x}")

        elif debug_command == "help":
            print("Available debug commands:")
            print("  r N          - Run next N instructions")
            print("  r            - Resume normal execution")
            print("  reg xN       - Print register xN (e.g., reg x10)")
            print("  reg all      - Print all general-purpose registers")
            print("  pc           - Print current PC")
            print("  csr          - Print CSR register values")
            print("  help         - Show this help message")
            print("  exit         - Exit the simulation")

        else:
            print("Unavailable command. Type 'help' to see available commands.")

def execute_instruction(format, opcode, func3, func7, rd, rs1, rs2, imm, inst):
    global pc
    if format == "R":
        result = executeR(opcode, rd, rs1, rs2, func3, func7, inst)
        pc += 4
    elif format == "I":
        result = executeI(opcode, rd, rs1, imm, func3, inst)
        pc += 4
    elif format == "S":
        result = executeS(opcode, rd, rs1, rs2, imm, func3, func7, inst)
        pc += 4
    elif format == "B":
        result = executeB(opcode, rs1, rs2, rd, func3, func7, imm, inst)
        pc += 4
    elif format == "U":
        result = executeU(opcode, rd, imm, inst)
        pc += 4
    elif format == "Supervisor":
        result = executeSupervisor(opcode, rd, rs1, rs2, imm, func3, func7, inst)
    elif format == "J":
        old_pc = pc
        result = executeJ(opcode, rd, imm, inst)
        if pc == old_pc:
            pc += 4
    else:
        scause.set_cause_by_description("Illegal instruction")
        handle_exception(inst)
        return "Illegal"
    return result

# Main loop for simulation
def simulate():
    global pc, debug_mode
    numb_inst = 0
    try:
        with open("text.bin", "r") as f:
            instructions = f.readlines()

        while pc // 4 < len(instructions):
            numb_inst += 1
            if numb_inst > 100:
                break

            inst = instructions[pc // 4].strip()
            if inst[0] == 'E':
                scause.set_cause_by_description("Illegal instruction")
                handle_exception(pc)
                continue

            format, opcode, func3, func7, rd, rs1, rs2, imm = instDecoder(inst)

            if debug_mode:
                run_debug_loop(instructions)
            else:
                run_normal_instruction(format, opcode, func3, func7, rd, rs1, rs2, imm, inst)

            registerFiles['0'] = 0

    except FileNotFoundError:
        print("Error: text.bin file not found!")
    except Exception as e:
        print(f"Execution error: {e}")

# Main program
def write_to_file():
    with open("datamem_register.bin", "w", encoding="utf-8") as file1, open("datamem.bin", "w", encoding="utf-8") as file2:
        global pc
        file1.write("pc: " + str(pc) + "\n")
        
        # Ghi thông tin Register Files
        file1.write("Register Files:\n")
        for reg, value in registerFiles.items():
            file1.write(f"x{reg}: {value}\n")
        # Ghi thông tin các thanh ghi Supervisor (CSR)
        file1.write("\nSupervisor CSRs:\n")
        if sstatus.read() != "00000000000000000000000000000000":
            file1.write("sstatus: " + sstatus.read() + "\n")
            file1.write("Active important bits:" + "\n"  + sstatus.check_important_bits() + "\n")

        if stvec.read() != "00000000000000000000000000000000":
            file1.write("\nstvec: " + stvec.read() + "\n")
            file1.write("Active important bits:"+ "\n"  +  str(stvec.check_important_bits()) + "\n")
        
        if sip.read() != "00000000000000000000000000000000":
            file1.write("\nsip: " + sip.read() + "\n")
            file1.write("Active important bits:"+ "\n"  + str(sip.check_important_bits()) + "\n")
        if sie.read() != "00000000000000000000000000000000":
            file1.write("\nsie: " + sie.read() + "\n")
            file1.write("Active important bits:"+ "\n"  + str(sie.check_important_bits()) + "\n")

        if scounteren.read() != "00000000000000000000000000000000":
            file1.write("\nscounteren: " + scounteren.read() + "\n")
            file1.write("Active important bits:"+ "\n"  + str(scounteren.check_important_bits()) + "\n")

        if sscratch.read() != "00000000000000000000000000000000":
            file1.write("\nsscratch: " + sscratch.read() + "\n")
            file1.write("Active important bits:"+ "\n"  + str(sscratch.check_important_bits()) + "\n")

        if sepc.read() != "00000000000000000000000000000000":
            file1.write("\nsepc: " + sepc.read() + "\n")
            file1.write("Active important bits:"+ "\n"  + str(sepc.check_important_bits()) + "\n")
            
        if scause.read() != "00000000000000000000000000000000":
            file1.write("\nscause: " + scause.read() + "\n")
            file1.write("Active important bits:"+ "\n"  + str(scause.check_important_bits()) + "\n")

        if stval.read() != "00000000000000000000000000000000":
            file1.write("\nstval: " + stval.read() + "\n")
            file1.write("Active important bits:" + "\n" + str(stval.check_important_bits()) + "\n")

        if senvcfg.read() != "00000000000000000000000000000000":
            file1.write("\nsenvcfg: " + senvcfg.read() + "\n")
            file1.write("Active important bits:"+ "\n"  + str(senvcfg.check_important_bits()) + "\n")

        if satp.read() != "00000000000000000000000000000000":
            file1.write("\nsatp: " + satp.read() + "\n")
            file1.write("Active important bits:"+ "\n"  + str(satp.check_important_bits()) + "\n")



        file1.write("\nData Memory:\n")
        for addr, data in sorted(dataMemory.items()):
            file1.write(f"0x{addr:08X}: {data}\n")
        
        file1.write("\nI/O:\n")
        for io, data in IO.items():
            file1.write(f"{str(io)}: {data}\n")

            
        # Chọn start_addr/end_addr cố định
        start_addr = 0x00000000
        end_addr = 0x00001fe0
        # Duyệt qua toàn bộ vùng nhớ từ start_addr đến end_addr với bước 32 byte
        for base_addr in range(start_addr, end_addr + 1, 32):
            file2.write(f"0x{base_addr:08x} ")  # Địa chỉ in bằng chữ thường
            line_data = []
            
            # Lấy dữ liệu của 8 giá trị trên mỗi dòng (mỗi giá trị cách nhau 4 byte)
            for offset in range(0, 32, 4):
                addr = base_addr + offset
                if addr in dataMemory:
                    line_data.append(f"{dataMemory[addr]:10d}")  # Giá trị hệ thập phân, căn phải
                else:
                    line_data.append(f"{0:10d}")  # Nếu không có dữ liệu, hiển thị 0
            
            # Ghi dữ liệu của dòng vào file, cách nhau một khoảng trống
            file2.write("    ".join(line_data) + "\n")

if __name__ == "__main__":
    simulate()
    # Ghi kết quả ra file
    write_to_file()

