
# from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib import rcParams
import numpy as np
import os
import pandas as pd
from pathlib import Path
from scipy.signal import find_peaks
import xlsxwriter



plt.style.use('seaborn-v0_8-whitegrid')
rcParams['figure.facecolor'] = 'white'
rcParams['savefig.facecolor'] = 'white'
rcParams['font.family'] = 'serif'
rcParams['font.sans-serif'] = ['Times New Roman']
rcParams['font.style'] = 'normal'
plt.rcParams['mathtext.default'] = 'regular'


STARTDIR = '//10.23.0.9/Work - Dsystems/ПРОЕКТЫ/Испытания Дагестанский ППУ/Испытания на вибростоле'
INFO_FILE = 'D:/Вибрация/Дагестанский ППУ/Дагестанский ППУ.xlsx'
FORCE_FILE = Path(__file__).parent / 'Force_set.txt'


def alignYaxes(axes, align_values=None):
    '''Align the ticks of multiple y axes

    Args:
        axes (list): list of axes objects whose yaxis ticks are to be aligned.
    Keyword Args:
        align_values (None or list/tuple): if not None, should be a list/tuple
            of floats with same length as <axes>. Values in <align_values>
            define where the corresponding axes should be aligned up. E.g.
            [0, 100, -22.5] means the 0 in axes[0], 100 in axes[1] and -22.5
            in axes[2] would be aligned up. If None, align (approximately)
            the lowest ticks in all axes.
    Returns:
        new_ticks (list): a list of new ticks for each axis in <axes>.

        A new sets of ticks are computed for each axis in <axes> but with equal
        length.
    '''
    from matplotlib.pyplot import MaxNLocator

    nax=len(axes)
    ticks=[aii.get_yticks() for aii in axes]
    if align_values is None:
        aligns=[ticks[ii][0] for ii in range(nax)]
    else:
        if len(align_values) != nax:
            raise Exception("Length of <axes> doesn't equal that of <align_values>.")
        aligns=align_values

    bounds=[aii.get_ylim() for aii in axes]

    # align at some points
    ticks_align=[ticks[ii]-aligns[ii] for ii in range(nax)]

    # scale the range to 1-100
    ranges=[tii[-1]-tii[0] for tii in ticks]
    lgs=[-np.log10(rii)+2. for rii in ranges]
    igs=[np.floor(ii) for ii in lgs]
    log_ticks=[ticks_align[ii]*(10.**igs[ii]) for ii in range(nax)]

    # put all axes ticks into a single array, then compute new ticks for all
    comb_ticks=np.concatenate(log_ticks)
    comb_ticks.sort()
    locator=MaxNLocator(nbins='auto', steps=[1, 2, 2.5, 3, 4, 5, 8, 10])
    new_ticks=locator.tick_values(comb_ticks[0], comb_ticks[-1])
    new_ticks=[new_ticks/10.**igs[ii] for ii in range(nax)]
    new_ticks=[new_ticks[ii]+aligns[ii] for ii in range(nax)]

    # find the lower bound
    idx_l=0
    for i in range(len(new_ticks[0])):
        if any([new_ticks[jj][i] > bounds[jj][0] for jj in range(nax)]):
            idx_l=i-1
            break

    # find the upper bound
    idx_r=0
    for i in range(len(new_ticks[0])):
        if all([new_ticks[jj][i] > bounds[jj][1] for jj in range(nax)]):
            idx_r=i
            break

    # trim tick lists by bounds
    new_ticks=[tii[idx_l:idx_r+1] for tii in new_ticks]

    # set ticks for each axis
    for axii, tii in zip(axes, new_ticks):
        axii.set_yticks(tii)

    return new_ticks



def find_res_width2(array, freqs, peak_pos):
    """ finds resonance width according to GOST R 56801-2015 """
    n = 2**0.5

    # left border
    for idx in range(peak_pos,0,-1):
        if array[idx] <= array[peak_pos]/n:
            break
    f1 = freqs[idx] + (array[peak_pos]/n - array[idx])/(array[idx+1] - array[idx])*(freqs[idx+1] - freqs[idx])
    
    # right border
    for idx in range(peak_pos, len(array)-1):
        if array[idx] <= array[peak_pos]/n:
            break
    f2 = freqs[idx-1] + (array[peak_pos]/n - array[idx-1])/(array[idx] - array[idx-1])*(freqs[idx] - freqs[idx-1])
            
    return f1, f2


def read_ecofizika(file, axes):
    """Reads data from Ecofizika (Octava)"""
    vibration = pd.read_csv(file, sep='\t', encoding='mbcs', header=None, names=axes,
                            dtype=np.float32,
                            skiprows=4, usecols=range(1,len(axes)+1)).reset_index(drop=True)
    inf = pd.read_csv(file, sep=' ', encoding='mbcs', header=None, names = None,
                           skiprows=2, nrows=1).reset_index(drop=True)
    fs = int(inf.iloc[0, -1])

    return vibration, fs


def save_xlsx(datas,
              colnames=['Частота, Гц','Передаточчная функция','Эффективность, дБ'],
              sheet_names=None,
              extra_res=None,
              name='Rez',
              savedir=os.getcwd()):

    workbook = xlsxwriter.Workbook(f'{savedir}/{name}.xlsx', {'strings_to_numbers':True})

    if sheet_names == None:
        sheet_names = list(datas.keys())
    for i in range(len(datas)):
        M = list(datas.keys())[i]
        try:
            _save_xlsx_sheet(workbook, sheet_names[i], datas[M], colnames, extra_res[M])
        except (KeyError, TypeError):
            _save_xlsx_sheet(workbook, sheet_names[i], datas[M], colnames)

    workbook.close()
    print(f'{name}.xlsx is saved to: {savedir}')

    
def _save_xlsx_sheet(workbook, sheet_name, datas, colnames, extra_res=None):
    
    num_format = workbook.add_format({
        'num_format': 'General',
        'font_name': 'Times New Roman',
        'font_size': 9})
    cell_format = workbook.add_format({
        'font_name': 'Times New Roman',
        'font_size': 9,
        'align': 'center',
        'text_wrap': True})
    
    worksheet = workbook.add_worksheet(str(sheet_name))
    
    for j in range(len(datas)):
        
        worksheet.write(0, j, f'{colnames[j]}', cell_format)
        
        for i in range(len(datas[j])):
            worksheet.write(i+1, j,
                           f'{datas[j][i]}', num_format)
            
    if extra_res != None:
        worksheet.write(0, len(datas)+1, 'Частота, Гц', cell_format)
        worksheet.write(0, len(datas)+2, 'Динамический модуль упругости, МПа', cell_format)
        worksheet.write(0, len(datas)+3, 'Коэффициент потерь', cell_format)
        
        for i in range(len(extra_res)):
            worksheet.write(1, i+len(datas)+1,
                           f'{extra_res[i]}', num_format)
    
    
def vibraTableMany(series, startdir, sizes, heights, SR11_files, limits = [0, 200], loads = [2, 5, 10], NFFT = 2048, overlap = 256):
    
    axes = ['1','2']
    # series = [48]
    # loads = [2, 5, 10]   # kg
    # NFFT = 2048
    # overlap = 256
    # limits = [0, 200]   # Hz
    
    images = {}
    
    for batch in series:
        # Finding folder (date) in startdir that contains folder with desired series
    
        folders = []
    
        for date in os.listdir(startdir):
            try:
                datefolder = os.path.join(startdir, date)
                folders.extend([os.path.join(datefolder, i) for i in os.listdir(datefolder) if i.startswith(str(batch))])
    #             if len(folders) > 0:
    #                 break
            except NotADirectoryError:
                pass
    #     print(folders)
        for folder in folders:
            name = os.path.basename(folder)
            images[name] = {}
            # print(name)
            a = sizes.loc[name,:].iloc[0] *1e-3   # size of one side (m)
            b = sizes.loc[name,:].iloc[1] *1e-3   # size of another side (m)
            S = a*b   # sampe area (m2)
        
            for M in loads:
            
                project_name = os.path.basename(folder) + '_' + str(M) + 'кг'   # used for saving, e.g. '44.1_5кг'
            
                h = heights.loc[name, :].iloc[loads.index(M)] *1e-3   # sample height (m)
            
                vibration_list, fs = read_ecofizika(os.path.join(folder, f'{M}.csv'), axes)
            
                rms1 = np.sqrt(np.mean(np.square(vibration_list['1'])))
                rms2 = np.sqrt(np.mean(np.square(vibration_list['2'])))
            
                if rms1 < rms2 :
                    axes = ['2','1']
                    vibration_list.columns = axes
            
                # make fft for Dagestan PPU
                Pxx = {}
                freqs_ = {}
    #             w = np.hamming(NFFT)
                with plt.ioff():
                    for ax in axes:

                        fig2, axs = plt.subplots(figsize=(10, 5), tight_layout=True)

                        y = vibration_list[ax].iloc[0*fs:]

                        Pxx[ax], freqs_[ax], bins, im = axs.specgram(y, NFFT=NFFT, Fs=fs, 
                                                                    mode='magnitude', 
                    #                                                 window=w,
                                                                    noverlap=overlap, cmap='viridis')
    #                     fig2.colorbar(im, label='dB/Hz')
    #                 #     plt.ylim(0, 250)
    #                     axs.set_title(f'$ Датчик\ {ax} $', fontsize=14)
    #                     axs.set_xlabel('$ Время,\ с $', fontsize=12)
    #                     axs.set_ylabel('$ Частота,\ Гц $', fontsize=12)
    #                     axs.grid(visible='True', which='both', axis='both', ls='--')
                
                last_index = int(limits[1] / freqs_['1'][1])
                freqs = freqs_['1'][1:last_index]
    
                TR1 = np.mean(Pxx['2'][1:last_index] / Pxx['1'][1:last_index], axis=1)
                TR = np.mean(Pxx['1'][1:last_index] / Pxx['2'][1:last_index], axis=1)
                TR1mean = pd.Series(TR1).rolling(5, min_periods=1, center=True).mean()
                TRmean = pd.Series(TR).rolling(5, min_periods=1, center=True).mean()

                L = 20*np.log10(TR)
                Lmean = 20*np.log10(TRmean)

            
                fig1, axs = plt.subplots(2, 1, figsize=(10, 8), tight_layout=True)
            
                axs[0].plot(freqs, TR1)
                axs[0].plot(freqs, TR1mean)
                axs[0].set_title('Передаточная функция')
                axs[0].set_ylabel('Модуль передаточной функции')
                axs[0].set_xlabel('Частота, Гц')
                axs[0].grid(visible='True', which='both', axis='both', ls='--')
    #             axs[0].set_xlim([0, 200])


                axs[1].plot(freqs, L)
                axs[1].plot(freqs, Lmean)
            
                axs[1].set_title('Эффективность виброизоляции')
                axs[1].set_ylabel('Эффективность, дБ')
                axs[1].set_xlabel('Частота, Гц')
                axs[1].grid(visible='True', which='both', axis='both', ls='--')
    #             axs[1].set_xlim([0, 200])
            
                try:
                    max1 = 5
                    f_peaks = find_peaks(TR1, distance=100, prominence=1)
        #             f_height = -1*f_peaks[1]['peak_heights']
                    f_peak_pos = f_peaks[0][0]
                    Fpeak = freqs[f_peak_pos]

                    f1, f2 = find_res_width2(TR1mean, freqs, f_peak_pos)
                    if f1 < 0:
                        raise ValueError('f1 < 0')
                    damp = (f2 - f1) / Fpeak
                    Ed = 4*np.pi**2 * Fpeak**2 *M *h / S *1e-6  # dynamic modulus of elasticity
                
                    axs[0].plot(Fpeak, TR1mean[f_peak_pos], "o", mfc='none', color = "r", linewidth=3, )
                    # axs[0].axhline(y=TR1mean[f_peak_pos].values/2**0.5, color="purple", linestyle="--", linewidth=0.5)
                    axs[0].axvline(x=f1, color="black", linestyle="--", linewidth=0.5)
                    axs[0].axvline(x=f2, color="black", linestyle="--", linewidth=0.5)
                    axs[0].annotate(f"Dynamic modulus of elasticity = {Ed:.5f} MPa\n"\
                                    f"Damping = {damp:.5f}",
                                    xy=(Fpeak, TR1mean[f_peak_pos]),
                                    xytext=(10, 0), textcoords="offset points",
                                    horizontalalignment="left",
                                    verticalalignment="center"
                                   )
                
                    axs[1].plot(Fpeak, Lmean[f_peak_pos], "o", mfc='none', color = "r", linewidth=3, )
                
                except IndexError:
                    import warnings
                    warnings.warn(f'There was a problem findind peak in {project_name} or with some other Index', UserWarning)
                except ValueError as err:
                    print(err)
                # plt.savefig(f'{project_name}.png', dpi=300)
                
                images[name][f'{project_name}.png'] = fig1
            
            
                ### Add data from Sylomer SR11
            
                SR11_list, SRfs = read_ecofizika(SR11_files[loads.index(M)], axes=['1','2'])
            
                SR_h = heights.loc['SR11', :].iloc[loads.index(M)] *1e-3   # sample height (m)
                SR_a = sizes.loc['SR11'].iloc[0] *1e-3
                SR_b = sizes.loc['SR11'].iloc[1] *1e-3
                SR_S = SR_a*SR_b   # sampe area (m2)
            
                SRPxx = {}
                with plt.ioff():
                    for ax in axes:

                        fig2, axs = plt.subplots(figsize=(10, 5), tight_layout=True)

                        y = SR11_list[ax].iloc[20*SRfs:]
                    
                        # make fft for Sylomer
                        SRPxx[ax], _, _, _ = axs.specgram(y, NFFT=NFFT, Fs=SRfs, 
                                                          mode='magnitude',
    #                                                       window=w,
                                                          noverlap=overlap, cmap='viridis')
            
                SR_TR1mean = np.mean(SRPxx['2'][1:last_index] / SRPxx['1'][1:last_index], axis=1)
                SR_TRmean = np.mean(SRPxx['1'][1:last_index] / SRPxx['2'][1:last_index], axis=1)
            
                SR_Lmean = 20*np.log10(SR_TRmean)
            
                fig3, axs = plt.subplots(2, 1, figsize=(10, 8), tight_layout=True)
            
                axs[0].plot(freqs, SR_TR1mean, label='SR11')
                axs[0].plot(freqs, TR1mean, label=f'ППУ-{name}')
                axs[0].set_title('Передаточная функция')
                axs[0].set_ylabel('Модуль передаточной функции')
                axs[0].set_xlabel('Частота, Гц')
                axs[0].legend(loc='upper right', fontsize=10, frameon=True)
                axs[0].grid(visible='True', which='both', axis='both', ls='--')
    #             axs[0].set_xlim([0, 200])


                axs[1].plot(freqs, SR_Lmean, label='SR11')
                axs[1].plot(freqs, Lmean, label=f'ППУ-{name}')
            
                axs[1].set_title('Эффективность виброизоляции')
                axs[1].set_ylabel('Эффективность, дБ')
                axs[1].set_xlabel('Частота, Гц')
                axs[1].legend(loc='lower right', fontsize=10, frameon=True)
                axs[1].grid(visible='True', which='both', axis='both', ls='--')
    #             axs[1].set_xlim([0, 200])
    
            
                # plt.savefig(f'{project_name}+SR11.png', dpi=300)
                images[name][f'{project_name}+SR11.png'] = fig3
            
                # Save Excel
                # save_xlsx(datas = [freqs, TR1mean, Lmean], 
                #           colnames = ['Частота, Гц','Передаточчная функция','Эффективность, дБ'],
                #           name = project_name)
                
    return images


def vibraTableOne(name, files, a, b, h, heights, loads, axes=['2','1'], NFFT=2048, overlap=256, limits=(0, 200), left_lim=5):
    images = {}
    datas = {}
    results = {}

    S = a*b *1e-6  # sampe area (m2)
    
    fig1, axs1 = plt.subplots(2, 1, figsize=(10, 8), tight_layout=True)
    axs1[0].set_title('Передаточная функция')
    axs1[0].set_ylabel('Модуль передаточной функции')
    axs1[0].set_xlabel('Частота, Гц')
    axs1[0].grid(visible='True', which='both', axis='both', ls='--')

    axs1[1].set_title('Эффективность виброизоляции')
    axs1[1].set_ylabel('Эффективность, дБ')
    axs1[1].set_xlabel('Частота, Гц')
    axs1[1].grid(visible='True', which='both', axis='both', ls='--')
    
    
    
    # Fpeaks, Eds, damps = {}, {}, {}
    # all_freqs, all_TR1mean, all_Lmean = {}, {}, {}
    
    
    for M in loads:

        project_name = name + '_' + str(M) + 'кг'   # used for saving, e.g. '44.1_5кг'
        
        _h = heights[loads.index(M)] *1e-3   # sample height (m)
        
        vibration_list, fs = read_ecofizika(files[loads.index(M)], axes)
        rms1 = np.sqrt(np.mean(np.square(vibration_list['1'])))
        rms2 = np.sqrt(np.mean(np.square(vibration_list['2'])))
        
        # if rms1 < rms2 :
        #     vibration_list.columns = ['2','1']
        
        # make fft for Dagestan PPU
        Pxx = {}
        freqs_ = {}
        # w = np.hamming(NFFT)
        with plt.ioff():
            for ax in axes:

                fig2, axs = plt.subplots(figsize=(10, 5), tight_layout=True)

                y = vibration_list[ax].iloc[0*fs:]

                # spectrogram
                Pxx[ax], freqs_[ax], _, _ = axs.specgram(y, NFFT=NFFT, Fs=fs, 
                                                            mode='magnitude',
                                                            noverlap=overlap, cmap='viridis')

            
        last_index = int(limits[1] / freqs_['1'][1])
        freqs = freqs_['1'][1:last_index]
        left_lim_idx = np.argmax(freqs>left_lim)   # for finding peak located at frequency greater then 3 Hz

        TR1 = np.mean(Pxx['2'][1:last_index] / Pxx['1'][1:last_index], axis=1)
        TR = np.mean(Pxx['1'][1:last_index] / Pxx['2'][1:last_index], axis=1)
        TR1mean = pd.Series(TR1).rolling(10, min_periods=1, center=True).mean()
        TRmean = pd.Series(TR).rolling(10, min_periods=1, center=True).mean()

        L = 20*np.log10(TR)
        Lmean = 20*np.log10(TRmean)
        
        datas[M] = (freqs, TR1mean, Lmean)
        
        axs1[0].plot(freqs, TR1mean, label=f'{M} кг')
        axs1[1].plot(freqs, Lmean, label=f'{M} кг')

        
        fig2, axs = plt.subplots(2, 1, figsize=(10, 8), tight_layout=True)
        
        axs[0].plot(freqs, TR1)
        axs[0].plot(freqs, TR1mean)
        axs[0].set_title('Передаточная функция')
        axs[0].set_ylabel('Модуль передаточной функции')
        axs[0].set_xlabel('Частота, Гц')
        axs[0].grid(visible='True', which='both', axis='both', ls='--')
#             axs[0].set_xlim([0, 200])


        axs[1].plot(freqs, L)
        axs[1].plot(freqs, Lmean)
        
        axs[1].set_title('Эффективность виброизоляции')
        axs[1].set_ylabel('Эффективность, дБ')
        axs[1].set_xlabel('Частота, Гц')
        axs[1].grid(visible='True', which='both', axis='both', ls='--')
#             axs[1].set_xlim([0, 200])
        
        try:
            max1 = TR1mean[left_lim_idx:].max()
            f_peaks = find_peaks(TR1mean[left_lim_idx:], distance=100, prominence=0.1*max1)
#             f_height = -1*f_peaks[1]['peak_heights']
            f_peak_pos = f_peaks[0][0]+left_lim_idx
            Fpeak = freqs[f_peak_pos]
            
            axs[0].plot(Fpeak, TR1mean[f_peak_pos], "o", mfc='none', color = "r", linewidth=3, )

            f1, f2 = find_res_width2(TR1mean, freqs, f_peak_pos)
            if f1 < 0:
                raise ValueError('f1 < 0')
            damp = (f2 - f1) / Fpeak
            Ed = 4*np.pi**2 * Fpeak**2 *M *_h / S *1e-6  # dynamic modulus of elasticity
            
            results[M] = (Fpeak, Ed, damp)
            
            
            # axs[0].axhline(y=TR1mean[f_peak_pos].values/2**0.5, color="purple", linestyle="--", linewidth=0.5)
            axs[0].axvline(x=f1, color="black", linestyle="--", linewidth=0.5)
            axs[0].axvline(x=f2, color="black", linestyle="--", linewidth=0.5)
            axs[0].annotate(f"Dynamic modulus of elasticity = {Ed:.5f} MPa\n"\
                            f"Damping = {damp:.5f}\n"\
                            f"Frequency = {Fpeak:.2f} Hz",
                            xy=(Fpeak, TR1mean[f_peak_pos]),
                            xytext=(10, 0), textcoords="offset points",
                            horizontalalignment="left",
                            verticalalignment="center"
                            )
            
            axs[1].plot(Fpeak, Lmean[f_peak_pos], "o", mfc='none', color = "r", linewidth=3, )
            
        except IndexError:
            import warnings
            warnings.warn(f'Не найден пик при нагрузке {M} кг, или другая проблема с индексацией при этой нагрузке', UserWarning)
        except ValueError as err:
            print(err)
        
        images[f'{project_name}.png'] = fig2
        
        """
            ### Add data from Sylomer SR11 to pictures
        
            SR11_list, SRfs = read_ecofizika(SR11[loads.index(M)], axes=['1','2'])
        
            SR_h = heights.loc['SR11', :].iloc[loads.index(M)] *1e-3   # sample height (m)
            SR_a = sizes.loc['SR11'].iloc[0] *1e-3
            SR_b = sizes.loc['SR11'].iloc[1] *1e-3
            SR_S = SR_a*SR_b   # sampe area (m2)
        
            SRPxx = {}
            with plt.ioff():
                for ax in axes:

                    fig2, axs = plt.subplots(figsize=(10, 5), tight_layout=True)

                    y = SR11_list[ax].iloc[20*SRfs:]
                
                    # make fft for Sylomer
                    SRPxx[ax], _, _, _ = axs.specgram(y, NFFT=NFFT, Fs=SRfs, 
                                                      mode='magnitude',
#                                                       window=w,
                                                      noverlap=overlap, cmap='viridis')
        
            SR_TR1mean = np.mean(SRPxx['2'][1:last_index] / SRPxx['1'][1:last_index], axis=1)
            SR_TRmean = np.mean(SRPxx['1'][1:last_index] / SRPxx['2'][1:last_index], axis=1)
        
            SR_Lmean = 20*np.log10(SR_TRmean)
        
            fig3, axs = plt.subplots(2, 1, figsize=(10, 8), tight_layout=True)
        
            axs[0].plot(freqs, SR_TR1mean, label='SR11')
            axs[0].plot(freqs, TR1mean, label=f'ППУ-{name}')
#             axs[0].plot(freqs, TR1mean, label=f'{name}')
            axs[0].set_title('Передаточная функция')
            axs[0].set_ylabel('Модуль передаточной функции')
            axs[0].set_xlabel('Частота, Гц')
            axs[0].legend(loc='upper right', fontsize=10, frameon=True)
            axs[0].grid(visible='True', which='both', axis='both', ls='--')
#             axs[0].set_xlim([0, 200])


            axs[1].plot(freqs, SR_Lmean, label='SR11')
            axs[1].plot(freqs, Lmean, label=f'ППУ-{name}')
        
            axs[1].set_title('Эффективность виброизоляции')
            axs[1].set_ylabel('Эффективность, дБ')
            axs[1].set_xlabel('Частота, Гц')
            axs[1].legend(loc='lower right', fontsize=10, frameon=True)
            axs[1].grid(visible='True', which='both', axis='both', ls='--')
#             axs[1].set_xlim([0, 200])
        
            plt.savefig(f'{project_name}+SR11.png', dpi=300)
        """
        
    axs1[0].legend(loc='upper right', fontsize=10, frameon=True)
    axs1[1].legend(loc='lower right', fontsize=10, frameon=True)
    
    try:
        if len(results) >= 2:
            fig3, axs3 = plt.subplots(1, 1, figsize=(10, 5), tight_layout=True)
            fig3.subplots_adjust(right=0.75)

            twin1 = axs3.twinx()
            twin2 = axs3.twinx()
            twin2.spines.right.set_position(("axes", 1.1))
            
            pressures = [load / S * 9.81 *1e-3 for load in loads]
            all_heights = [h]
            all_heights.extend(heights)

            p1, = axs3.plot(range(len(results)+1), all_heights, "C0", linewidth=2, label="Толщина")
            p2, = twin1.plot(range(1, len(results)+1), [results[load][1] for load in loads], "C1", linewidth=2, label="Динамический модуль упругости")
            p3, = twin2.plot(range(1, len(results)+1), [results[load][2] for load in loads], "C2", linewidth=2, label="Коэффициент демпфирования")

            axs3.set(xlim=(0, len(results)), xlabel="Нагрузка, кг (кПа)", ylabel="Толщина, мм")
            # axs3.set_ylim(bottom=0)
            twin1.set(ylabel="Динамический модуль упругости, МПа")
            # twin1.set_ylim(bottom=0)
            twin2.set(ylabel="Коэффициент демпфирования")
            # twin2.set_ylim(bottom=0)

            axs3.yaxis.label.set_color(p1.get_color())
            twin1.yaxis.label.set_color(p2.get_color())
            twin2.yaxis.label.set_color(p3.get_color())
            
            
            axs3.set_xticks(range(len(results)+1))
            xlabels = [0]
            xlabels.extend([f'{load} ({pressure:.2f})' for load, pressure in zip(loads, pressures)])
            axs3.set_xticklabels(xlabels)

            axs3.tick_params(axis='y', colors=p1.get_color())
            axs3.grid(visible='True', which='both', axis='both', ls='--')
            twin1.tick_params(axis='y', colors=p2.get_color())
            # twin1.grid(visible='True', which='major', axis='y', ls='--', color=p2.get_color())
            twin2.tick_params(axis='y', colors=p3.get_color())
            # twin2.grid(visible='True', which='major', axis='y', ls='--', color=p3.get_color())
            alignYaxes((axs3,twin1,twin2))

            axs3.legend(handles=[p1, p2, p3])
        
        images[f'{name}.png'] = fig1
        
    except (IndexError,KeyError) as err:
        import warnings
        warnings.warn(f'Не найден пик, сводный график не будет построен', UserWarning)
        print(err)
        
    try:
        images[f'{name}_rez.png'] = fig3
    except UnboundLocalError:
        pass
    
    return (images, datas, results)



def read_static_txt(file):
    """Reads data from Static test"""
    df = pd.read_table(file, sep=',', encoding='mbcs', header=None, 
                     names = ['P1','P2','P3','Force_low','Force_high'],
                     usecols=range(1, 6)
                    ).reset_index(drop=True)
    
    return df
    
def save_static_xlsx(datas, colnames, name, savedir=os.getcwd()):
    import xlsxwriter
    
    if len(datas) != len(colnames):
        raise SyntaxError('Number of datas mismatch column names')

    workbook = xlsxwriter.Workbook(f'{savedir}/{name}.xlsx', {'strings_to_numbers':  True})

    num_format = workbook.add_format({
        'num_format': 'General',
        'font_name': 'Times New Roman',
        'font_size': 9})
    cell_format = workbook.add_format({
        'font_name': 'Times New Roman',
        'font_size': 9,
        'align': 'center',
        'text_wrap': True})
    
    worksheet = workbook.add_worksheet()
    
    for j in range(len(datas)):
        
        worksheet.write(0, j, f'{colnames[j]}', cell_format)
        
        for i in range(len(datas[j])):
            worksheet.write(i+1, j,
                           f'{datas[j][i]}', num_format)

    workbook.close()
    print(f'{name}.xlsx is saved to: {savedir}')
    
    

def staticTableOne(name, file, a, b, h, P1=25, P2=25, P3=25, forcemeter=500, cut_start=0, cut_end=1, init_force=None):
    images = {}
    datas = {}
    results = {}

    fs = 80
    
    F1_coeff = pd.read_table(FORCE_FILE, encoding='mbcs', header=None, 
                             skiprows=10, usecols=[0,1], index_col=0
                             ).loc[forcemeter]
    # if forcemeter == '500':
    #     F1_coeff = 896.18
    # elif forcemeter == '200':
    #     F1_coeff = 2245.32
    # elif forcemeter == '5000':
    #     F1_coeff = 86.01
    # else:
    #     F1_coeff = float(forcemeter)
    
    P_num = 0   # number of working progibomers (deflection meters)
    if P1 == 'нет':
        P1_coeff = 0
    else:
        P_num += 1
        P1_coeff = int(P1)/4095
    if P2 == 'нет':
        P2_coeff = 0
    else:
        P_num += 1
        P2_coeff = int(P2)/4095
    if P3 == 'нет':
        P3_coeff = 0
    else:
        P_num += 1
        P3_coeff = int(P3)/4095
    
    
    try:

        data = read_static_txt(file).iloc[cut_start*fs:-1*cut_end*fs].reset_index(drop=True)
        
        # load converted to N
        force = (data['Force_low'].iloc[:].mask(
            (data['Force_low'].iloc[:]- data['Force_low'].iloc[0]
                > (data['Force_low'].iloc[:]- data['Force_low'].iloc[0]).mean()*5)
        ).interpolate()
                    - data['Force_low'].iloc[0]
                ) * F1_coeff[1]/8388608*2*9.81
        
        
        # interpolate one more time
        force = force.mask((force > force.mean()*3)).interpolate()
        force = force.mask((force < 0)
                            ).interpolate().rolling(150, min_periods=1, center=True).mean()
        
        if init_force == None:
            # init_force = 0.01*force.max()
            init_force = 1
        force_start = force[force > init_force].index[0]

        # time converted to s
        t = np.arange(len(force)) / fs


        # deflection as mean deflection from all 3 deflection meters, converted to mm
        defl = ((
                (data['P1'] - (data['P1']).iloc[force_start]).mask(
                    (data['P1'] - (data['P1']).iloc[force_start]) < 0
                ).interpolate() * P1_coeff
                
                + (data['P2'] - (data['P2']).iloc[force_start]).mask(
                    (data['P2'] - (data['P2']).iloc[force_start]) < 0
                ).interpolate() * P2_coeff

                + (data['P3'] - (data['P3']).iloc[force_start]).mask(
                    (data['P3'] - (data['P3']).iloc[force_start]) < 0
                ).interpolate() * P3_coeff
            ) 
                / P_num
        ).rolling(120, min_periods=1, center=True).mean()

        defl = defl.mask(defl - defl.iloc[force_start] <= 0, 0)


        # determine each load cycle
        max1 = (-1*force).min()*0.3
        prominence = (-1*force).min()*0.2
        f_peaks = find_peaks(-1*force, distance=15*fs, height=max1, prominence=abs(prominence), width=10)
        if len(f_peaks[0]) == 0:
            raise(TypeError)
        f_height = -1*f_peaks[1]['peak_heights']
        if f_peaks[0][-1] > len(force)-5000:
            f_peak_pos = np.concatenate(([0], f_peaks[0]))
        else:
            f_peak_pos = np.concatenate(([0], f_peaks[0], [len(defl)-1]))#

        ## finding relaxation
        x = np.arange(f_peak_pos[-2]+4000, f_peak_pos[-1]-6000)
        x2 = np.arange(f_peak_pos[-2], f_peak_pos[-1])
        # approximation `y = k*x + l`
        k, l = np.polyfit(x,
                            y = defl.iloc[f_peak_pos[-2]+4000 : f_peak_pos[-1]-6000],
                            deg=1)

        ''' looking for the first and last value with error less than 0.01 
        with respect to linear interpolation on the last load cycle '''
        mask = abs(defl.iloc[f_peak_pos[-2] : f_peak_pos[-1]] - k*x2 - l) < 0.02
#         plateau_start = defl.iloc[f_peak_pos[-2] : f_peak_pos[-1]][mask].index[0]
        plateau_end = defl.iloc[f_peak_pos[-2] : f_peak_pos[-1]][mask].index[-1]
        indmax = force.iloc[f_peak_pos[-2]:f_peak_pos[-1]].idxmax()
        plateau_start = indmax



        #!!! First picture -- time-deflection & time-load -- !!!

        fig, axs = plt.subplots(figsize=(10, 5), tight_layout=True)

        axs.plot(t,
                    defl, 
                    label='Средний прогиб', color='C0')
        axs.plot(t[plateau_start], defl[plateau_start], "x", color = "g", linewidth=3, )
        axs.plot(t[plateau_end], defl[plateau_end], "x", mfc='none', color="magenta", linewidth=3, )

        axs.tick_params(axis='y', which='both', labelcolor='C0')
        axs.set_ylabel('Перемещение, мм', fontsize=12, color='C0')

        axs2 = axs.twinx()
        axs2.plot(t,
                    force,
                    label='Нагрузка', color='C1')
        axs2.plot(t[plateau_start], force[plateau_start], "x", color = "g", linewidth=3, )
        axs2.plot(t[plateau_end], force[plateau_end], "x", mfc='none', color="magenta", linewidth=3, )
        axs2.plot(t[f_peak_pos], force[f_peak_pos], "o", mfc='none', color = "r", linewidth=3, )

        axs2.tick_params(axis='y', which='both', labelcolor='C1', direction='out', length=6, color='C1')
        axs2.set_ylabel('Нагрузка, Н', fontsize=12, color='C1')
        axs2.grid(visible=None)
        axs.set_xlabel('Время, с', fontsize=12)
        axs.grid(visible='True', which='both', axis='both', ls='--')

        images[f'{name}_нагрузка.png'] = fig



        #!!! Second picture -- load - deflection per each cycle -- !!!

        fig2, axs = plt.subplots(figsize=(10, 5), tight_layout=True)

        for i in range(len(f_peak_pos)-1):
            axs.plot(defl.iloc[f_peak_pos[i]:f_peak_pos[i+1]],
                        force.iloc[f_peak_pos[i]:f_peak_pos[i+1]],
                        label=f'Цикл {i+1}')

        axs.set_ylabel('Нагрузка, Н', fontsize=12)
        axs.set_xlabel('Перемещение, мм', fontsize=12)
        axs.legend(loc='lower right', fontsize=10, frameon=True)
        axs.grid(visible='True', which='both', axis='both', ls='--')

        images[f'{name}_циклы.png'] = fig2




        #!!! Third picture -- last (4th) load-defrlection cycle only -- !!!

        fig3, axs = plt.subplots(figsize=(10, 5), tight_layout=True)

        axs.plot(defl.iloc[f_peak_pos[-2]:f_peak_pos[-1]],
                    force.iloc[f_peak_pos[-2]:f_peak_pos[-1]],
                    label='Цикл 4')
        axs.plot(defl[plateau_start], force[plateau_start], "x", mfc='none', color = "g", linewidth=3, )
        axs.plot(defl[plateau_end], force[plateau_end], "x", mfc='none', color="magenta", linewidth=3, )

        relax = force[plateau_start] - force[plateau_end]
        relax_t = (plateau_end - plateau_start) / fs

        axs.annotate(f"R = {relax:.1f} Н\n"\
                        f"t = {relax_t:.1f} с",
                        xy=(defl[plateau_start], 0),
                        xytext=(-10, 10), textcoords="offset points",
                        horizontalalignment="right",
                        verticalalignment="bottom"
                    )

        axs.set_ylabel('Нагрузка, Н', fontsize=12)
        axs.set_xlabel('Перемещение, мм', fontsize=12)
        axs.grid(visible='True', which='both', axis='both', ls='--')

        images[f'{name}_4цикл.png'] = fig3

        

        #!!! -- 4th picture -- Elasticity modulus + define form-factor -- !!!

        form = a*b / (2*h*(a+b))
        try:
            indmin = defl.iloc[
                f_peak_pos[-2]:indmax][defl.iloc[f_peak_pos[-2]:indmax] < defl.iloc[f_peak_pos[-2]]+0.01
                                        ].index[-1]
        except IndexError:
            indmin = f_peak_pos[-2]
        epsylon = ((defl.iloc[indmin:indmax] - defl.iloc[indmin])
                    / h *1e2).reset_index(drop=True)   # convert to m/m (%)
        stress = (force.iloc[indmin:indmax] / (a*b) ).reset_index(drop=True)  # convert to MPa, 1 MPa = 1 N/mm**2 
        elasticity = stress / (epsylon*1e-2)  # convert to MPa
        elasticity_max = 1.1 * elasticity.iloc[100:].max()
        elasticity_min = 0.9 * elasticity.min()

        fig4, axs = plt.subplots(2, 1, figsize=(10, 8), tight_layout=True)

        axs[0].plot(stress[1:],
                    elasticity[1:])
        axs[0].set_ylim(top=elasticity_max, bottom=elasticity_min)
        axs[0].set_title(f'Коэффициент формы q={form:.4f}')
        axs[0].set_xlabel('Удельное давление, МПа', fontsize=12)
        axs[0].set_ylabel('Модуль упругости, МПа', fontsize=12)
        axs[0].grid(visible='True', which='both', axis='both', ls='--')

        axs[1].plot(stress[1:],
                    epsylon[1:])
        axs[1].set_xlabel('Удельное давление, МПа', fontsize=12)
        axs[1].set_ylabel('Относительная деформация, %', fontsize=12)
        axs[1].grid(visible='True', which='both', axis='both', ls='--')

        images[f'{name}_elastic.png'] = fig4
        
        datas['force'] = force.iloc[f_peak_pos[-2]:f_peak_pos[-1]].reset_index(drop=True)
        datas['deflection'] = defl.iloc[f_peak_pos[-2]:f_peak_pos[-1]].reset_index(drop=True)
        
        
        results['stress'] = stress
        results['epsylon'] = epsylon
        results['elasticity'] = elasticity
        results['relax'] = relax
        results['relax_t'] = relax_t
        
        for i in range(1, len(epsylon)):
            if (epsylon[1] < 10) and (epsylon[i] >= 10):
                results['defl_10'] = stress[i]
                break
        for i in range(i, len(epsylon)):
            if (epsylon[1] < 20) and (epsylon[i] >= 20):
                results['defl_20'] = stress[i]
                break
        for i in range(i, len(epsylon)):
            if (epsylon[1] < 40) and (epsylon[i] >= 40):
                results['defl_40'] = stress[i]
                break

        # # Save Excel
        # if save:
        #     save_xlsx(datas = [stress, epsylon, elasticity],
        #                 colnames = ['Удельная нагрузка, МПа','Относительная деф-я, %','Модуль упругости, МПа'],
        #                 name = name)

        #     # Save Excel with initial data
        #     save_xlsx(datas = [force.iloc[f_peak_pos[-2]:f_peak_pos[-1]].reset_index(drop=True),
        #                         defl.iloc[f_peak_pos[-2]:f_peak_pos[-1]].reset_index(drop=True),
        #                         ],
        #                 colnames = ['Нагрузка, Н','Перемещение, мм'],
        #                 name = f'{name}_load-deflection')

    except TypeError:
        fig, axs = plt.subplots(figsize=(10, 5), tight_layout=True)
        axs.plot(t,
                    defl, 
                    label='Средний прогиб', color='C0')
        axs.tick_params(axis='y', which='both', labelcolor='C0')
        axs.set_ylabel('Перемещение, мм', fontsize=12, color='C0')
        axs2 = axs.twinx()
        axs2.plot(t,
                    force,
                    label='Нагрузка', color='C1')
        axs2.tick_params(axis='y', which='both', labelcolor='C1', direction='out', length=6, color='C1')
        axs2.set_ylabel('Нагрузка, Н', fontsize=12, color='C1')
        axs2.grid(visible=None)
        axs.set_xlabel('Время, с', fontsize=12)
        axs.grid(visible='True', which='both', axis='both', ls='--')
        
        images[f'{name}_нагрузка.png'] = fig
        
        
        # if save:
        #     plt.savefig(f'{name}_нагрузка.png', dpi=300)
        #     save_xlsx(datas = [force.iloc[f_peak_pos[-2]:f_peak_pos[-1]].reset_index(drop=True),
        #                             defl.iloc[f_peak_pos[-2]:f_peak_pos[-1]].reset_index(drop=True),
        #                             ],
        #                     colnames = ['Нагрузка, Н','Перемещение, мм'],
        #                     name = f'{name}_load-deflection')
            
    return (images, datas, results)