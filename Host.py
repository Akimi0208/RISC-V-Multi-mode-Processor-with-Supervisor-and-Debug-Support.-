from ISS import RISCV_ISS
from DebugModule import DebugModule
input_loaded = False
RISCV = RISCV_ISS()
DM = DebugModule(RISCV)
def main():
    global input_loaded
    global DM
    while(1):
        print("===Multi-mode RISCV Processor with Supervisor and Debug Support Simulator===")
        print("Please enter your instruction: ")
        Host_Command = input()
        if Host_Command == "input":
            if input_loaded == False:
                file = input("Enter your input file name: ")
                RISCV.load_program_from_binary_file(file)
                print("Load file completed!")
                input_loaded = True
        elif Host_Command == "dmp":
            if input_loaded == False:
                print("Please load your input first!")
            else:
                RISCV.dump_loaded_instructions()
                print("Dump file completed!!")
        elif Host_Command == "Umode":
            if input_loaded == False:
                print("Please load your input first!")
            else:
                RISCV.privilege_level = 0b00
                print("Running as User mode...")
                execute()
        elif Host_Command == "Smode":
            if input_loaded == False:
                print("Please load your input first!")
            else:
                RISCV.privilege_level = 0b01
                print("Running as Supervisor mode...")
                execute()
        elif Host_Command == "Dmode":
            if input_loaded == False:
                print("Please load your input first!")
            else:
                RISCV.privilege_level = 0b00
                print("Running as Debug mode...")
                DM.enter_debug_mode
        elif Host_Command == "help":
            print("=====Available Instructions=====")
            print(" input    - Load input (binary file)")
            print(" dmp      - Dump currentt input file")
            print(" Umode    - Run as User mode")
            print(" Smode    - Run as Supervisor mode")
            print(" Dmode    - Run as Debug mode")
            print(" exit     - Exit simulation")
        elif Host_Command == "exit":
            print("Exit Simulation!")
            exit()
        else:
                print("Unknown command. Type 'help' to see available commands.")
    
def execute():
    global RISCV
    global DM
    global input_loaded
    while(1):
        print("Please enter your instruction: ")
        Execute_Command = input()
        if Execute_Command == "r":
            RISCV.step()
        elif Execute_Command == "run all":
            while (RISCV.load_word(int(RISCV.pc))!=0):
                RISCV.step()
            print("Simulation Completed!")
        elif Execute_Command == "reset":
            RISCV = RISCV_ISS()
            DM = DebugModule(RISCV)
            input_loaded = False
            print("Simulation reset! Please reload the program.")
            break
        elif Execute_Command == "debug mode":
            DM.enter_debug_mode()
        elif Execute_Command == "help":
            print("=====Available Instructions=====")
            print(" r           - run 1 instruction")
            print(" run all     - run to the end")
            print(" reset       - reset all instructions")
            print(" debug mode  - enter debug mode")
            print(" help        - display available instruction")
            print(" exit        - End simulation")
        elif Execute_Command == "exit":
            print("Exit Simulation!")
            exit()
        else:
            print("Unknown command. Type 'help' to see available commands.")
if __name__ == "__main__":
    main()