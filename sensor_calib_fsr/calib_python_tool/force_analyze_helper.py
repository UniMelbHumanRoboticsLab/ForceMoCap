import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from sklearn.metrics import r2_score

def scatter_quant_mag(force_df:pd.DataFrame,quantity=["B","F"],case="Train"):
    fig1,axs  = plt.subplots(1,2, figsize=(10,5),constrained_layout=True)
    fig1.suptitle(f"{case} - {quantity}", fontsize=16)

    x = force_df[f'{quantity[0]}']
    y = force_df[f'{quantity[1]}']

    axs[0].scatter(x,y, label=f'{quantity[0]}-{quantity[1]}',s=5)
    axs_0_title = f'{quantity[0]} - {quantity[1]} Scatter'
    axs[1].plot(x, label=f'{quantity[0]}')
    axs[1].plot(y, label=f'{quantity[1]}', linestyle='--')
    
    if "F_pred" in quantity:
        r2 = r2_score(x,y)
        axs_0_title += f' (R2: {r2:.2f})'
        print(f"R2 Score: {r2:.2f}")
        xlim = axs[0].get_xlim()
        ylim = axs[0].get_ylim()
        range_max = max(abs(xlim[1] - xlim[0]), abs(ylim[1] - ylim[0]))

        # Center the axes and apply equal range
        x_center = sum(xlim) / 2
        y_center = sum(ylim) / 2

        mini = np.min([x_center - range_max/2,y_center - range_max/2])
        maxi = np.max([x_center + range_max/2,y_center + range_max/2])
        

        x = [mini,maxi] 
        y = [mini,maxi] 
        # print(x,y)
        axs[0].plot(x,y, label=f'ideal',c = 'k')
        axs[0].set_xlim(x_center - range_max/2, x_center + range_max/2)
        axs[0].set_ylim(y_center - range_max/2, y_center + range_max/2)
        axs[0].set_aspect('equal', adjustable='box')
    
    axs[0].set_title(axs_0_title)
    axs[0].set_xlabel(f'{quantity[0]}')
    axs[0].set_ylabel(f'{quantity[1]}')
    axs[0].grid(True)
    axs[0].legend()

    axs[1].set_title(f'{quantity[0]} - {quantity[1]} Time')
    axs[1].set_xlabel(f't')
    axs[1].set_ylabel(f'{quantity[0]}')
    axs[1].grid(True)
    axs[1].legend()

def range_quant_mag(force_df:pd.DataFrame,quantity="F",case="Train"):
    force_range = np.array(force_df[f'{quantity}'].agg(['min', 'max']).tolist())
    # print(f"{case} - {quantity}\n\n")
    # print(f"{quantity}: {force_range[0]:.2f} - {force_range[1]:.2f}")
    # print(f"# points: {force_df.shape[0]}\n\n")

    return force_range
def hist_quant_mag(force_df:pd.DataFrame,quantity="F",case = "Train"):
    fig, axs = plt.subplots(1,1, figsize=(7, 7))
    fig.suptitle(f"{case} - {quantity}", fontsize=16)
    sns.histplot(data=force_df, x=f'{quantity}', kde=True, color="skyblue", ax=axs)

def analyze_quant(force_df:pd.DataFrame,quantity="F",case="Train",mag=False):
    if mag:
        range_quant_mag(force_df,quantity=quantity,case=case)
        hist_quant_mag(force_df=force_df,quantity=quantity,case=case)
