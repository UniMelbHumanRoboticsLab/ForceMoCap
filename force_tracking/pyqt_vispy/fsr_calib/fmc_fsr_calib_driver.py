# driver.py
import subprocess, sys, os,json

SCRIPT = os.path.join(os.path.dirname(__file__), "fmc_fsr_calib.py")

id_key = {
    "f1": 0,
    "f2": 1,
    "f3": 2,
    "f4": 3,
    "f5": 4,
    "p1": 5,
    "p2": 6,
    "p3": 7,
    "p4": 8,
}
side = "right"
finger = "p4"
finger_id = id_key[finger]
print(f"{side} {finger} on!")

for take_num in [0,1,2,3]:
    argv ={"gui_freq":60,
            "init_flags":{"esp":1,
                          "rft":1,
                          "log":1,
                          "gui_3d_on":False,
                          "force_gui":{"on?":True,"RFT":True,"ESP":True}},
            "side":side,
            "finger_name":finger,
            "finger_id":finger_id,
            "take_num":take_num,
            "RFT":"COM5",
            # "ESP":{"sides":["left","right"],"ports":[4211,4212],"ips":["192.168.240.121","192.168.240.27"],"server_ports":[4213,4214]},
            # "SS":{"sides":["left","right"],"ports": [9004,9003]}}

            "ESP":{"sides":["right"],"ports":[4212],"ips":["192.168.240.27"],"server_ports":[4214]}}
            # "SS":{"sides":["right"],"ports": [9003]}}

            # "ESP":{"sides":["left"],"ports":[4211],"ips":["192.168.240.121"],"server_ports":[4213]}}
            # "SS":{"sides":["left"],"ports": [9004]}}
    argv = json.dumps(argv)
    
    print(f"=== Session {take_num} ===")
    rc = subprocess.call(
        [sys.executable, SCRIPT,str(argv)],
        env=os.environ,
    )
    if rc != 0:
        print(f"Session {take_num} exited with {rc}, stopping.")
        break

    # go_on = input("Continue?: y/n: ")
    # while (go_on != "y" and go_on != "n"):
    #     go_on = input("Continue?: Reenter y/n: ")
    # if go_on == "y":
    #     pass
    # elif go_on == "n":
    #     break
print(f"{side} {finger} done!")