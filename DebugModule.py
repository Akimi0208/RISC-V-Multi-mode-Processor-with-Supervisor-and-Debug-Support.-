from ISS import RISCV_ISS
from CSR import CSR32, DCSR, DPC, DScratch0, DScratch1

class DebugModule:
    def __init__(self, iss: RISCV_ISS):
        self.iss = iss  # Instance of ISS (1 hart)
        self.in_debug_mode = False
        self.breakpoints = set()
        # Debug CSRs
        self.dcsrs = {
            "dcsr": DCSR(),
            "dpc": DPC(),
            "dscratch0": DScratch0(),
            "dscratch1": DScratch1(),
        }

        # Control flags
        self.single_step = False
        self.pending_step = False

    def enter_debug_mode(self, cause="Ebreak"):
        if not self.in_debug_mode:
            self.in_debug_mode = True
            self.dcsrs["dcsr"].set_debug_cause(cause)
            self.dcsrs["dpc"].write(f"{self.iss.pc:032b}")  # Save PC as binary string
            print(f"[DEBUG] Entered debug mode due to {cause} at PC=0x{self.iss.pc:08x}")

            while True:
                debug_command = input("Please enter your command: ").strip()

                if debug_command.startswith("r "):
                    try:
                        run_count = int(debug_command.split()[1])
                        for i in range(run_count):
                            self.iss.step()
                            if self.check_breakpoint():
                                break
                        print(f"[DEBUG] Stepped {run_count} instruction(s).")
                    except ValueError:
                        print("Invalid format. Use: r N (e.g., r 5)")

                elif debug_command == "resume":
                    self.exit_debug_mode()
                    break

                elif debug_command == "exit":
                    print("[DEBUG] Exiting simulation.")
                    exit()

                elif debug_command.startswith("reg x"):
                    try:
                        if "=" in debug_command:
                            # Ghi giá trị vào thanh ghi
                            lhs, rhs = debug_command.split("=")
                            reg_str = lhs.strip()[5:]
                            reg_num = int(reg_str)
                            value_str = rhs.strip()
                            value = int(value_str, 0)  # hỗ trợ 0x, 0b, thập phân

                            if 0 <= reg_num <= 31:
                                self.write_gpr(reg_num, value)  # <- dùng hàm write_gpr()
                                print(f"[WRITE] x{reg_num} <= 0x{value:08x}")
                            else:
                                print("Register number must be between 0 and 31.")
                        else:
                            # Đọc giá trị
                            reg_num = int(debug_command[5:])
                            if 0 <= reg_num <= 31:
                                val = self.iss.regs[reg_num]
                                print(f"x{reg_num} = 0x{val:08x}")
                            else:
                                print("Register number must be between 0 and 31.")
                    except ValueError:
                        print("Invalid command format. Use: reg xN or reg xN = VALUE")


                elif debug_command == "reg all":
                    print("==== General Purpose Registers (x0 - x31) ====")
                    for i in range(32):
                        val = self.iss.regs[i]
                        print(f"x{i:02} = 0x{val:08x}", end="\t")
                        if (i + 1) % 4 == 0:
                            print()
                    print("==============================================")

                elif debug_command == "pc":
                    print(f"PC = 0x{self.iss.pc:08x}")

                elif debug_command == "csr":
                    print("==== CSR Registers ====")
                    for name, csr in self.iss.csrs.items():
                        print(f"{name.upper()}: 0b{int(csr.read(), 2):032b}")
                    print("=============================")
                    
                elif debug_command == "dcsr":
                    print("==== CSR Debug Registers ====")
                    for name, csr in self.dcsrs.items():
                        print(f"{name.upper()}: 0b{int(csr.read(), 2):032b}")
                    print("=============================")
                
                elif debug_command.startswith("break "):
                    try:
                        addr_str = debug_command.split()[1]
                        addr = int(addr_str, 0)  # Cho phép 0x... hoặc thập phân
                        self.set_breakpoint(addr)
                    except (IndexError, ValueError):
                        print("Usage: break <address>. Example: break 0x100")

                elif debug_command == "help":
                    print("Available debug commands:")
                    print("  break        - Place a breakpoint")
                    print("  r N          - Run next N instructions")
                    print("  resume       - Resume normal execution")
                    print("  reg xN       - Print register xN (e.g., reg x10)")
                    print("  reg xN =     - Write register xN (e.g., reg x10 = 46)")
                    print("  reg all      - Print all general-purpose registers")
                    print("  pc           - Print current PC")
                    print("  csr          - Print CSR register values")
                    print("  dcsr         - Print Debug CSR register values")
                    print("  help         - Show this help message")
                    print("  exit         - Exit the simulation")

                else:
                    print("Unknown command. Type 'help' to see available commands.")


    def exit_debug_mode(self):
        if self.in_debug_mode:
            self.in_debug_mode = False
            self.iss.pc = self.dcsrs["dpc"].read()
            print(f"[DEBUG] Exiting debug mode, resuming at PC=0x{int(self.iss.pc, 2):08x}")
            
    # Requirement 1: Debugger gets implementation info
    def get_implementation_info(self):
        # Can include: number of harts, supported features, etc.
        return {
            "hart_count": 1,
            "supports_halt_resume": True,
            "abstract_access_supported": True,
            "xlen": 32,
        }

    # Requirement 2: Halt the hart
    def halt_hart(self):
        if not self.in_debug_mode:
            self.in_debug_mode = True
            self.dcsrs["dpc"].write(f"{self.iss.pc:032b}")
            self.dcsrs["dcsr"].halted = 1  # Custom flag inside DCSR to indicate halted
            print("Hart halted.")

    # Requirement 2: Resume the hart
    def resume_hart(self):
        if self.in_debug_mode:
            self.in_debug_mode = False
            self.iss.pc = int(self.dcsrs["dpc"].read(), 2)
            self.dcsrs["dcsr"].halted = 0
            print("Hart resumed.")

    # Requirement 3: Status on halted hart
    def is_hart_halted(self) -> bool:
        return self.dcsrs["dcsr"].halted == 1

    # Requirement 4: Abstract read access to GPRs
    def read_gpr(self, reg_index: int) -> int:
        if not self.in_debug_mode:
            raise Exception("Cannot read register: hart not halted")
        if not (0 <= reg_index < 32):
            raise ValueError("Register index out of range")
        return self.iss.regs[reg_index]

    # Requirement 4: Abstract write access to GPRs
    def write_gpr(self, reg_index: int, value: int):
        if not self.in_debug_mode:
            raise Exception("Cannot write register: hart not halted")
        if not (0 <= reg_index < 32):
            raise ValueError("Register index out of range")
        if reg_index != 0:  # x0 is always zero
            self.iss.regs[reg_index] = value & 0xFFFFFFFF  # enforce 32-bit

    def set_breakpoint(self, addr: int):
        self.breakpoints.add(addr)
        print(f"[DEBUG] Breakpoint set at 0x{addr:08x}")

    def check_breakpoint(self):
        if self.iss.pc in self.breakpoints:
            print(f"[DEBUG] Breakpoint hit at 0x{self.iss.pc:08x}")
            self.enter_debug_mode("Breakpoint")
            return True
        return False
