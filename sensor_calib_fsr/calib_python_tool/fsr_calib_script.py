from glob import glob
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import pickle
import os

from sklearn.metrics import r2_score
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler,PolynomialFeatures
from force_analyze_helper import *

# 1-1 linear regression with SGD optimization 
def fit_model(force_df:pd.DataFrame):
    y = force_df["F"].values
    x = force_df[["1/R"]].values

    reg = make_pipeline(StandardScaler(),
                        LinearRegression())
    reg.fit(x, y)
        
    return reg
def pred_model(force_df:pd.DataFrame,calib_matrix):
    y = force_df["F"].values
    x = force_df[["1/R"]].values
    y_pred = calib_matrix.predict(x)

    error_matrix = np.absolute(y-y_pred)

    error_df = pd.DataFrame(error_matrix, columns=["dF"])
    pred_df = pd.DataFrame(y_pred, columns=["F_pred"])
    return pd.concat([force_df,pred_df,error_df], axis=1)

if __name__ == "__main__":
    for hand in ["left","right"]:
        for sensor in ["f1","f2","f3","f4","f5","p1","p2","p3","p4"]:
            # training sample
            models = ["linreg_sgd_1_1"]
            for model in models:
                print("===========================================================")
                # print(model)

                # train samples
                calib_df = []
                for iter in [0,1]:
                    cur_force_df = pd.read_csv(f"sensor_calib_fsr/data/{hand}/{sensor}/force_{iter}.csv")
                    calib_df.append(cur_force_df)
                calib_df = pd.concat(calib_df)
                calib_df = calib_df.reset_index()
                # analyze_quant(calib_df,"F","Train",mag=True)                
                # scatter_quant_mag(calib_df,["F","1/R"],case=f"Train")
                
                # calibration matrix
                calib_matrix = fit_model(calib_df)

                # print("Training Eval")
                pred_df = pred_model(force_df=calib_df,calib_matrix=calib_matrix)
                # analyze_quant(pred_df,quantity="dF",case="Train Eval",mag=True)
                # scatter_quant_mag(pred_df,["F","F_pred"],case="Train Eval")
                
                # test samples
                
                for iter in [3]:
                    test_df = []
                    cur_force_df = pd.read_csv(f"sensor_calib_fsr/data/{hand}/{sensor}/force_{iter}.csv")
                    test_df.append(cur_force_df)
                    test_df = pd.concat(test_df)
                    test_df = test_df.reset_index()

                    # print(f"Test {iter} Eval")
                    pred_df = pred_model(force_df=test_df,calib_matrix=calib_matrix)
                    # analyze_quant(pred_df,quantity="dF",case=f"Test Eval",mag=True)
                    # scatter_quant_mag(test_df,["F","1/R"],case=f"Test Eval")
                    scatter_quant_mag(pred_df,["F","F_pred"],case=f"Test Eval")
                
                # save model and figures
                calib_path = os.path.join(f"./sensor_calib_fsr/data/{hand}/{sensor}", f"model_{hand}_{sensor}.pkl")
                print(calib_path)
                print(f"M={calib_matrix._final_estimator.coef_[0]:.2f},b={calib_matrix._final_estimator.intercept_:.2f}")
                with open(calib_path,'wb') as f:
                    pickle.dump(calib_matrix,f)

                # Get all PNG files in the directory
                import glob
                png_files = glob.glob(os.path.join(f"./sensor_calib_fsr/data/{hand}/{sensor}/analysis", "*.png"))
                
                # Remove each PNG file
                for file_path in png_files:
                    try:
                        os.remove(file_path)
                        # print(f"Removed: {file_path}")
                    except Exception as e:
                        print(f"Error removing {file_path}: {e}")

                for i, fig_num in enumerate(plt.get_fignums()):
                    fig = plt.figure(fig_num)
                    fig_path = os.path.join(f"./sensor_calib_fsr/data/{hand}/{sensor}/analysis", f"{i}.png")
                    fig.savefig(fig_path)
                # plt.tight_layout()
                plt.show()
                plt.close('all')