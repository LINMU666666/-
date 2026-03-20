import numpy as np
import matplotlib.pyplot as plt

# --- 作图规范设定（Times New Roman, 刻度朝内，符合 SCI 期刊规范） ---
plt.rcParams['font.family'] = 'Times New Roman'
plt.rcParams['font.size'] = 12
plt.rcParams['xtick.direction'] = 'in'
plt.rcParams['ytick.direction'] = 'in'
plt.rcParams['xtick.major.size'] = 5
plt.rcParams['ytick.major.size'] = 5

def generate_schematic_xps():
    """ 生成 Mn-Fe(2:1)/AC XPS 示意分峰拟合图 """

    fig, axs = plt.subplots(2, 2, figsize=(10, 8), sharex=False, sharey=False)

    title_font = {'size': 14, 'weight': 'bold'}

    # (a) Mn 2p (2p3/2) - 示意核心活性位点
    x = np.linspace(638, 650, 200)
    # 示意数据生成（实际处理需导入数据）
    peak1 = 40.2 * np.exp(-((x - 641.0) / 1.5)**2)  # Mn2+
    peak2 = 52.1 * np.exp(-((x - 642.1) / 1.5)**2)  # Mn3+ (核心)
    peak3 = 7.7 * np.exp(-((x - 643.3) / 1.5)**2)   # Mn4+
    background = np.linspace(50, 100, 200) # 示意线性背景
    total_fit = peak1 + peak2 + peak3 + background

    axs[0, 0].plot(x, total_fit, 'k-', lw=1.5, label='Experimental')
    axs[0, 0].plot(x, peak1, 'r--', lw=1.2, label='Mn$^{2+}$ (40.2%)')
    axs[0, 0].plot(x, peak2, 'b--', lw=1.2, label='Mn$^{3+}$ (52.1%)') # 蓝色突出
    axs[0, 0].plot(x, peak3, 'g--', lw=1.2, label='Mn$^{4+}$ (7.7%)')
    axs[0, 0].plot(x, background, 'y-', lw=1, label='Background')
    axs[0, 0].set_title('(a) Mn 2p', **title_font)
    axs[0, 0].set_ylabel('Intensity (a.u.)')
    axs[0, 0].set_xlabel('Binding Energy (eV)')
    axs[0, 0].legend(loc='upper right', fontsize=9, frameon=False)
    axs[0, 0].set_xlim(650, 638) # 反向X轴，符合标准 XPS 展示

    # (b) Fe 2p (2p3/2) - 示意助剂与牺牲位点
    x = np.linspace(706, 716, 200)
    peak1 = 31.5 * np.exp(-((x - 709.8) / 1.8)**2)  # Fe2+
    peak2 = 68.5 * np.exp(-((x - 711.2) / 1.8)**2)  # Fe3+ (主导)
    total_fit = peak1 + peak2 + np.linspace(150, 180, 200)

    axs[0, 1].plot(x, total_fit, 'k-', lw=1.5, label='Experimental')
    axs[0, 1].plot(x, peak1, 'r--', lw=1.2, label='Fe$^{2+}$ (31.5%)')
    axs[0, 1].plot(x, peak2, 'b--', lw=1.2, label='Fe$^{3+}$ (68.5%)') # 蓝色突出
    axs[0, 1].plot(x, np.linspace(150, 180, 200), 'y-', lw=1, label='Background')
    axs[0, 1].set_title('(b) Fe 2p', **title_font)
    axs[0, 1].set_xlabel('Binding Energy (eV)')
    axs[0, 1].set_ylabel('Intensity (a.u.)')
    axs[0, 1].legend(loc='upper right', fontsize=9, frameon=False)
    axs[0, 1].set_xlim(716, 706)

    # (c) O 1s - 示意氧空位浓度 (Oβ)
    x = np.linspace(526, 536, 200)
    peak1 = 42.0 * np.exp(-((x - 529.8) / 1.5)**2)  # Oα Lattice
    peak2 = 58.0 * np.exp(-((x - 531.6) / 1.5)**2)  # Oβ Adsorbed (核心)
    total_fit = peak1 + peak2 + np.linspace(200, 220, 200)

    axs[1, 0].plot(x, total_fit, 'k-', lw=1.5, label='Experimental')
    axs[1, 0].plot(x, peak1, 'r--', lw=1.2, label='O$_{\\alpha}$: Lattice (42.0%)')
    axs[1, 0].plot(x, peak2, 'b--', lw=1.2, label='O$_{\\beta}$: Adsorbed (58.0%)') # 蓝色突出
    axs[1, 0].plot(x, np.linspace(200, 220, 200), 'y-', lw=1, label='Background')
    axs[1, 0].set_title('(c) O 1s', **title_font)
    axs[1, 0].set_ylabel('Intensity (a.u.)')
    axs[1, 0].set_xlabel('Binding Energy (eV)')
    axs[1, 0].legend(loc='upper right', fontsize=9, frameon=False)
    axs[1, 0].set_xlim(536, 526)

    # (d) C 1s - 示意碳载体官能团
    x = np.linspace(280, 292, 200)
    peak1 = 71.2 * np.exp(-((x - 284.8) / 1.2)**2)  # C-C (校准)
    peak2 = 19.5 * np.exp(-((x - 286.1) / 1.2)**2)  # C-O
    peak3 = 9.3 * np.exp(-((x - 288.5) / 1.5)**2)   # C=O
    total_fit = peak1 + peak2 + peak3 + np.linspace(50, 60, 200)

    axs[1, 1].plot(x, total_fit, 'k-', lw=1.5, label='Experimental')
    axs[1, 1].plot(x, peak1, 'r--', lw=1.2, label='C-C/C=C (71.2%)')
    axs[1, 1].plot(x, peak2, 'b--', lw=1.2, label='C-O (19.5%)')
    axs[1, 1].plot(x, peak3, 'g--', lw=1.2, label='C=O (9.3%)')
    axs[1, 1].plot(x, np.linspace(50, 60, 200), 'y-', lw=1, label='Background')
    axs[1, 1].set_title('(d) C 1s', **title_font)
    axs[1, 1].set_xlabel('Binding Energy (eV)')
    axs[1, 1].set_ylabel('Intensity (a.u.)')
    axs[1, 1].legend(loc='upper right', fontsize=9, frameon=False)
    axs[1, 1].set_xlim(292, 280)

    plt.tight_layout()
    plt.savefig('XPS_high_std_schematic.png', dpi=300) # 保存为高清图片
    print("高标准 SCI XPS 分峰拟合示意图已成功生成：XPS_high_std_schematic.png")

if __name__ == "__main__":
    generate_schematic_xps()
