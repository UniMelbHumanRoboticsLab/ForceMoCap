# driver.py
import subprocess, sys, os,json

SCRIPT = os.path.join(os.path.dirname(__file__), "fmc_fsr_calib.py")

for take_num in range(10):
    argv ={"gui_freq":60,
            "init_flags":{"esp":1,
                          "rft":1,
                          "log":1,
                          "gui_3d_on":False,
                          "force_gui":{"on?":True,"RFT":True,"ESP":True}},
            "side":"left",
            "finger_name":"p4",
            "finger_id":8,
            "take_num":take_num,
            "RFT":"COM14",
            "ESP":{"sides":["left"],"ports":[4211]}}
    argv = json.dumps(argv)
    
    print(f"=== Session {take_num} ===")
    rc = subprocess.call(
        [sys.executable, SCRIPT,str(argv)],
        env=os.environ,
    )
    if rc != 0:
        print(f"Session {take_num} exited with {rc}, stopping.")
        break

    go_on = input("Continue?: y/n: ")
    while (go_on != "y" and go_on != "n"):
        go_on = input("Continue?: Reenter y/n: ")
    if go_on == "y":
        pass
    elif go_on == "n":
        break