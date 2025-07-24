handler_base_addr = "10000000000000000010100101100000" # Địa chỉ base handler
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
    def __init__(self, hart_id=0):
        super().__init__("dcsr")
        self.hart_id = hart_id               # ID của hart hiện tại
        self.halted = 0                      # Trạng thái halted (1 nếu bị dừng)
        self.step_enabled = 0               # Có đang bật chế độ step không
        self.cause = "Unknown"              # Chuỗi hiển thị nguyên nhân debug
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
        cause_bits = self.value[25:28]
        cause_dict = {
            "000": "Ebreak",
            "001": "Trigger",
            "010": "Single-step",
            "011": "Reset-haltreq"
        }
        self.cause = cause_dict.get(cause_bits, "Unknown")
        return self.cause

    def set_debug_cause(self, cause: str):
        cause_dict = {
            "Ebreak":       "000",
            "Trigger":      "001",
            "Single-step":  "010",
            "Reset-haltreq":"011"
        }
        cause_bits = cause_dict.get(cause)
        if cause_bits is None:
            raise ValueError(f"Invalid debug cause: {cause}")
        # Insert cause_bits into bits 25-27 (31 - i because MSB = bit 0)
        v = list(self.value)
        v[31 - DCSR_CAUSE2_BIT] = cause_bits[0]
        v[31 - DCSR_CAUSE1_BIT] = cause_bits[1]
        v[31 - DCSR_CAUSE0_BIT] = cause_bits[2]
        self.value = ''.join(v)
        self.cause = cause

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