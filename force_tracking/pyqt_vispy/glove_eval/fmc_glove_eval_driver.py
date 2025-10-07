# driver.py
import subprocess, sys, os,json
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import random

exe_a_list = [
    {
        "exe_id": "exe1a1.1",
        "wrench_type": ["force", "N"],
    },
    {
        "exe_id": "exe1a1.2",
        "wrench_type": ["force", "N"],
    },
    {
        "exe_id": "exe1a1.3",
        "wrench_type": ["force", "N"],
    },
    {
        "exe_id": "exe1a2.1",
        "wrench_type": ["force", "N"],
    },
    {
        "exe_id": "exe1a2.2",
        "wrench_type": ["force", "N"],
    },
    {
        "exe_id": "exe1a2.3",
        "wrench_type": ["force", "N"],
    }
]

exe_b_list = [
    {
        "exe_id": "exe1b1.1",
        "wrench_type": ["force", "N"],
    },
    {
        "exe_id": "exe1b1.2",
        "wrench_type": ["force", "N"],
    },
    {
        "exe_id": "exe1b1.3",
        "wrench_type": ["moment", "Nm"],
    },
    {
        "exe_id": "exe1b1.4",
        "wrench_type": ["moment", "Nm"],
    },
    {
        "exe_id": "exe1b1.5",
        "wrench_type": ["moment", "Nm"],
    },
    {
        "exe_id": "exe1b2.1",
        "wrench_type": ["force", "N"],
    },
    {
        "exe_id": "exe1b2.2",
        "wrench_type": ["force", "N"],
    },
    {
        "exe_id": "exe1b2.3",
        "wrench_type": ["moment", "Nm"],
    },
    {
        "exe_id": "exe1b2.4",
        "wrench_type": ["moment", "Nm"],
    },
    {
        "exe_id": "exe1b2.5",
        "wrench_type": ["moment", "Nm"],
    },
]

exercises_list = [exe_a_list, exe_b_list]
SCRIPT = os.path.join(os.path.dirname(__file__), "fmc_glove_eval.py")

subject_name = "sub1"
exp_id = "exp1"
# esp_info = {"sides":["left","right"],"ports":[4211,4212],"ips":["192.168.153.121","192.168.153.28"],"server_ports":[4213,4214]},
esp_info = {"sides":["right"],"ports":[4212],"ips":["192.168.153.28"],"server_ports":[4214]}
# esp_info:{"sides":["left"],"ports":[4211],"ip":["192.168.153.121"],"server_ports":[4213]},
# ss_info = {"sides":["left","right"],"ports": [9004,9003]}
ss_info = {"sides":["right"],"ports": [9003]}
# ss_info:{"sides":["left"],"ports": [9004]}}

for exe_cat in exercises_list:
    random.shuffle(exe_cat)
    for exercise in exe_cat:
        # show exercise to participant
        images_path = os.path.join(f"./experiments/{exp_id}/protocol/exercise_images", f"{exercise['exe_id']}.png")
        print()
        print("========================================================")
        print(images_path)
        img = mpimg.imread(images_path)
        plt.figure(figsize=(12, 12))  # width, height in inches
        plt.imshow(img)
        plt.axis('off')  # Hide axess
        plt.tight_layout()
        plt.show()


        if exercise["wrench_type"][0] == "force":
            wrench_levels = [5, 10, 15, 20]
        elif exercise["wrench_type"][0] == "moment":
            wrench_levels = [0.5,1,1.5,2]
        if exercise["exe_id"] == "exe1b1.1" or exercise["exe_id"] == "exe1b2.1":
            wrench_levels = [1]
        if exercise["exe_id"] == "exe1b1.5":
            wrench_levels = [0.25,0.5]
        if exercise["exe_id"] == "exe1b2.5":
            wrench_levels = [0.25,0.5,0.75,1]

        random.shuffle(wrench_levels)

        for wrench_level in wrench_levels:
            # print(wrench_level)
            argv ={"gui_freq":60,
                    "exp_id":exp_id,
                    "subject_name":subject_name,
                    "glove_performer":subject_name,
                    "exe_id":exercise["exe_id"],
                    "init_flags":{"vive":0,
                                    "esp":0,
                                    "ss":0,
                                    "rft":0,
                                    "log":1,
                                    "gui_3d_on":True,
                                    "wrench_gui":{"on?":True,"RFT":False,"ESP":False,"SS":False,"feedback":True}},
                    "wrench_type":exercise["wrench_type"]+[wrench_level],
                    "VIVE":2,
                    "RFT":"COM5",
                    "ESP":esp_info,
                    # "ESP":{"sides":["right"],"ports":[4212],"ips":["192.168.153.28"],"server_ports":[4214]},
                    # "ESP":{"sides":["left"],"ports":[4211],"ip":["192.168.153.121"]},
                    "SS":ss_info}
                    # "SS":{"sides":["right"],"ports": [9003]}}

            argv = json.dumps(argv)

            print(f"=== Session {exercise['exe_id']}_{wrench_level} started ===")
            rc = subprocess.call(
                [sys.executable, SCRIPT,str(argv)],
                env=os.environ,
            )
            if rc != 0:
                print(f"Session {exercise}_{wrench_level} exited with {rc}, stopping.")
                break

        go_on = input("Continue with next exercise?: y/n: ")
        while (go_on != "y" and go_on != "n"):
            go_on = input("Continue?: Reenter y/n: ")
        if go_on == "y":
            pass
        elif go_on == "n":
            break
        print("========================================================")
        print()