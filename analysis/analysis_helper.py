import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import pingouin as pg

from sklearn.metrics import root_mean_squared_error,mean_squared_error,mean_absolute_error

def scatter_quantities(force_df:pd.DataFrame,quantities=["B","F"],case="Train",corr=True):
    fig1,axs  = plt.subplots(1,2, figsize=(10,5),constrained_layout=True)
    fig1.suptitle(f"{case} - {quantities}", fontsize=16)

    x = force_df[f'{quantities[0]}']
    y = force_df[f'{quantities[1]}']

    axs[0].scatter(x,y, label=f'{quantities[0]}-{quantities[1]}',s=5)
    axs_0_title = f'{quantities[0]} - {quantities[1]} Scatter'
    axs[1].plot(x, label=f'{quantities[0]}')
    axs[1].plot(y, label=f'{quantities[1]}', linestyle='--')
    
    if corr:
        lm = pg.linear_regression(x,y)
        r2 = lm.r2.values[0]
        pearson = pg.corr(x,y,method='pearson').r.values[0]
        axs_0_title += f' (R2: {r2:.2f})-(Pearson\'s R: {pearson:.2f})'
        print(f"{case}- R2: {r2:.2f}\tR: {pearson:.2f}")

        ## Plot ideal line
        # Get current axis limits
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
    axs[0].set_xlabel(f'{quantities[0]}')
    axs[0].set_ylabel(f'{quantities[1]}')
    axs[0].grid(True)
    axs[0].legend()

    axs[1].set_title(f'{quantities[0]} - {quantities[1]} Time')
    axs[1].set_xlabel(f't')
    axs[1].set_ylabel(f'{quantities[0]}')
    axs[1].grid(True)
    axs[1].legend()
def diff_quantities(force_df:pd.DataFrame,quantities=["B","F"],case="Train"):
    x = force_df[f'{quantities[0]}']
    y = force_df[f'{quantities[1]}']

    diff = x - y
    max_diff = diff[np.argmax(np.abs(diff))]   
    mae = mean_absolute_error(x,y)
    mse = mean_squared_error(x,y)
    rmse = root_mean_squared_error(x,y)
    print(f"{case}- MSE: {mse:.2f}\tRMSE: {rmse:.2f}\tMAE: {mae:.2f}\t Max Diff: {max_diff:.2f}")

def compare_quantities(force_df:pd.DataFrame,quantities=["B","F"],case="Train",corr=True):
    scatter_quantities(force_df, quantities=quantities, case=case, corr=corr)
    diff_quantities(force_df, quantities=quantities, case=case)
    print()

def range_quantity(force_df:pd.DataFrame,quantities="F",case="Train"):
    force_range = np.array(force_df[f'{quantities}'].agg(['min', 'max']).tolist())
    return force_range
def histogram_quantity(force_df:pd.DataFrame,quantities="F",case = "Train"):
    fig, axs = plt.subplots(1,1, figsize=(7, 7))
    fig.suptitle(f"{case} - {quantities}", fontsize=16)
    sns.histplot(data=force_df, x=f'{quantities}', kde=True, color="skyblue", ax=axs)
def analyze_quantity(force_df:pd.DataFrame,quantities="F",case="Train",mag=False):
    if mag:
        range_quantity(force_df,quantities=quantities,case=case)
        histogram_quantity(force_df=force_df,quantities=quantities,case=case)