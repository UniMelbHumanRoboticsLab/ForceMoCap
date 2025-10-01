# driver.py
import subprocess, sys, os,json

SCRIPT = os.path.join(os.path.dirname(__file__), "fmc_glove_eval.py")

for take_num in range(10):
    argv ={"gui_freq":60,
            "init_flags":{"vive":0,
                            "esp":0,
                            "ss":0,
                            "rft":1,
                            "log":1,
                            "gui_3d_on":False,
                            "force_gui":{"on?":True,"RFT":False,"ESP":True,"SS":False}},
            "exp_id":"exp1",
            "subject_name":"CA",
            "glove_performer":"JQ",
            "take_num":take_num,
            "VIVE":3,
            "RFT":"COM4",
            "ESP":{"sides":["left"],"ports":[4211]},
            "SS":{"sides":["left","right"],"ports": [9004,9003]}}
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