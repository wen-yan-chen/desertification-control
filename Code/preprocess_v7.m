%% preprocess_v7.m —— 治沙工程（2026 CQU_MCM B 题）数据预处理主程序（MATLAB 版）
%  适配 MATLAB R2020b 及以上，只用内置函数（无需任何工具箱）
%  与 Python 版 preprocess_v7.py 一一对应，输出同一张表的等价结果
%
%  输入：Data/v7/processed/panel_monthly_raw.csv
%  输出：Data/v7/processed/panel_monthly_clean_matlab.csv
%        Figures/v7/pre_matlab.png
%
%  运行：在 MATLAB 中把"当前文件夹"切到本仓库根目录，直接运行 preprocess_v7
%  说明：抓取与合并（JSON→面板）由 Python 完成；MATLAB 负责清洗、派生与出图，
%        两语言在这一步的算法完全一致，便于交叉校验。

%% ========== 1. 路径配置（学生只需改这一块） ==============================
% Windows 示例：BASE = 'D:\CQU\大三上\比赛\美赛\第一次校赛';
% macOS/Linux 示例：BASE = '/Users/xxx/Desktop/desertification';
% 注意：路径中避免中文与空格；Windows 下用单引号或双反斜杠。
BASE = fileparts(fileparts(mfilename('fullpath')));
if isempty(BASE)
    BASE = pwd;                      % 直接运行脚本时退化为当前目录
end

IN_CSV  = fullfile(BASE, 'Data', 'v7', 'processed', 'panel_monthly_raw.csv');
OUT_DIR = fullfile(BASE, 'Data', 'v7', 'processed');
FIG_DIR = fullfile(BASE, 'Figures', 'v7');
OUT_CSV = fullfile(OUT_DIR, 'panel_monthly_clean_matlab.csv');
OUT_FIG = fullfile(FIG_DIR, 'pre_matlab.png');

TRAIN_YEARS = [2015 2022];           % 训练期：所有统计量只在这段上拟合
NDVI_SOIL = 0.05;  NDVI_VEG = 0.85;  % 像元二分端元
Z0 = 0.001; KAPPA = 0.40; CL = 6.7; RHO = 1.225; G = 9.81; UT = 5.0;
%% =========================================================================

fprintf('\n================ 步骤 0：读取原始面板 ================\n');
if ~isfile(IN_CSV)
    error(['找不到输入文件：%s\n' ...
           '排查：① 路径是否写错；② 是否先运行了 v7_fetch.py 与 v7_finalize_fetch.py；\n' ...
           '      ③ 文件是否被 Excel 占用。'], IN_CSV);
end
try
    T = readtable(IN_CSV, 'TextType', 'string', 'VariableNamingRule', 'preserve');
catch ME
    error('读取失败：%s\n请检查文件编码（应为 UTF-8）与格式。', ME.message);
end
T.date = datetime(T.date, 'InputFormat', 'yyyy-MM-dd');
T = sortrows(T, {'site', 'date'});
fprintf('读入 %d 行 × %d 列，站点 %d 个，时间 %s ~ %s\n', ...
    height(T), width(T), numel(unique(T.site)), ...
    datestr(min(T.date), 'yyyy-mm'), datestr(max(T.date), 'yyyy-mm'));

%% ========== 步骤 1：质量审计（预处理前） ================================
fprintf('\n================ 步骤 1：质量审计 ================\n');
keyVars = {'T2M','PRECTOTCORR','GWETROOT','WS10M_MAX','ndvi_mvc_qa'};
for k = 1:numel(keyVars)
    v = keyVars{k};
    nMiss = sum(ismissing(T.(v)) | isnan(T.(v)));
    fprintf('  %-14s 缺失 %4d 个（%.2f%%）\n', v, nMiss, 100*nMiss/height(T));
end
dupKey = height(T) - height(unique(T(:, {'site','date'}), 'rows'));
fprintf('  重复“站点-月份”行：%d\n', dupKey);

%% ========== 步骤 2：单位与聚合口径修正 ==================================
fprintf('\n================ 步骤 2：单位与口径 ================\n');
T.days_in_month = eomday(T.date.Year, T.date.Month);   % base MATLAB，兼容 R2020b
T.P_mm     = T.PRECTOTCORR .* T.days_in_month;              % mm/d → mm/月
T.SW_MJ    = T.ALLSKY_SFC_SW_DWN .* T.days_in_month;        % MJ/m2/d → MJ/m2/月
T.EVLAND_mm = T.EVLAND .* T.days_in_month;
T.ET0_hargreaves = hargreaves(T);                           % 含 0.408 换算
fprintf('  降水、辐射、蒸发已按月天数换算；ET0 用 Hargreaves 公式计算\n');

%% ========== 步骤 3：遥感质控与覆盖度派生 ================================
fprintf('\n================ 步骤 3：遥感质控 ================\n');
T.V_pct  = min(max((T.ndvi_mvc_qa - NDVI_SOIL) / (NDVI_VEG - NDVI_SOIL), 0), 1) * 100;
T.V_unqa = min(max((T.ndvi_mvc    - NDVI_SOIL) / (NDVI_VEG - NDVI_SOIL), 0), 1) * 100;
fprintf('  覆盖度有效值 %d/%d；质控后均值 %.2f%%（未质控 %.2f%%）\n', ...
    sum(~isnan(T.V_pct)), height(T), mean(T.V_pct,'omitnan'), mean(T.V_unqa,'omitnan'));

%% ========== 步骤 4：派生变量 ============================================
fprintf('\n================ 步骤 4：派生变量 ================\n');
us  = KAPPA * T.WS10M_MAX / log(10/Z0);
ust = KAPPA * UT / log(10/Z0);
q   = max(CL*RHO/G .* us.^2 .* (us - ust), 0);
isTrain = T.date.Year >= TRAIN_YEARS(1) & T.date.Year <= TRAIN_YEARS(2);
base = mean(q(isTrain), 'omitnan');
T.E  = q / base;
lo = prctile(T.GWETROOT(isTrain), 5);
hi = prctile(T.GWETROOT(isTrain), 95);
T.W = min(max((T.GWETROOT - lo) / (hi - lo), 0), 1);
T.AI = T.P_mm ./ T.ET0_hargreaves;
T.AI(T.ET0_hargreaves == 0) = NaN;
fprintf('  侵蚀指数 E：中位 %.3f；W 压到边界的比例 %.2f%%\n', ...
    median(T.E,'omitnan'), 100*mean(T.W <= 0));
% 动态端元覆盖度
T.V_dyn = nan(height(T),1);
sites = unique(T.site);
for i = 1:numel(sites)
    idx = T.site == sites(i);
    idxTr = idx & isTrain;
    lo2 = prctile(T.ndvi_mvc(idxTr), 5);  hi2 = prctile(T.ndvi_mvc(idxTr), 95);
    T.V_dyn(idx) = min(max((T.ndvi_mvc(idx) - lo2) / (hi2 - lo2), 0), 1) * 100;
end

%% ========== 步骤 5：缺失填补（线性<=2 月 -> 训练期同月气候态） ============
fprintf('\n================ 步骤 5：缺失填补 ================\n');
vars = {'V_pct','W'};
for k = 1:numel(vars)
    v = vars{k};
    n0 = sum(isnan(T.(v)));
    T.(v) = fillmissing(T.(v), 'linear', 'MaxGap', 2, 'EndValues', 'nearest');
    for i = 1:numel(sites)
        idx = T.site == sites(i);
        idxTr = idx & isTrain;
        months = month(T.date);
        for m = 1:12
            sel = idx & months == m & isnan(T.(v));
            if any(sel)
                ref = idxTr & months == m & ~isnan(T.(v));
                if any(ref)
                    T.(v)(sel) = mean(T.(v)(ref), 'omitnan');
                end
            end
        end
    end
    T.(v) = fillmissing(T.(v), 'linear', 'EndValues', 'nearest');
    fprintf('  %s：%d → %d\n', v, n0, sum(isnan(T.(v))));
end

%% ========== 步骤 6：异常值标记（只标记不删除） ==========================
fprintf('\n================ 步骤 6：异常值标记 ================\n');
outVars = {'P_mm','WS10M_MAX','GWETROOT'};
for k = 1:numel(outVars)
    v = outVars{k};
    T.(["flag_" v]) = isoutlier(T.(v), 'median');
    fprintf('  %-12s 标记 %d 个月\n', v, sum(T.(['flag_' v])));
end

%% ========== 步骤 7：保存 ================================================
fprintf('\n================ 步骤 7：保存 ================\n');
if ~isfolder(OUT_DIR), mkdir(OUT_DIR); end
writetable(T, OUT_CSV, 'Encoding', 'UTF-8');
info = dir(OUT_CSV);
fprintf('  %s（%.0f KB）\n', OUT_CSV, info.bytes/1024);

%% ========== 步骤 8：完整性校验 ==========================================
fprintf('\n================ 步骤 8：完整性校验 ================\n');
checks = struct( ...
    'n_rows', height(T), ...
    'n_sites', numel(unique(T.site)), ...
    'n_dup', height(T) - height(unique(T(:, {'site','date'}), 'rows')), ...
    'V_missing', sum(isnan(T.V_pct)), ...
    'W_out', sum(T.W < 0 | T.W > 1), ...
    'V_out', sum(T.V_pct < 0 | T.V_pct > 100));
disp(checks);
assert(checks.V_missing == 0 && checks.W_out == 0 && checks.V_out == 0, ...
    '完整性校验未通过：请检查填补与派生步骤');

%% ========== 步骤 9：前 10 行 / 后 5 行 ==================================
fprintf('\n================ 步骤 9：结果预览 ================\n');
show = {'site','date','P_mm','GWETROOT','W','ndvi_mvc_qa','V_pct','E'};
disp(head(T(:, show), 10));
disp(tail(T(:, show), 5));

%% ========== 步骤 10：可视化 ============================================
fprintf('\n================ 步骤 10：可视化 ================\n');
if ~isfolder(FIG_DIR), mkdir(FIG_DIR); end
f = figure('Color','w','Position',[100 100 1000 520]);
subplot(2,1,1);
sel = T.site == "YT";
plot(T.date(sel), T.V_unqa(sel), '.', 'Color',[0.87 0.42 0.13], 'MarkerSize',6); hold on;
plot(T.date(sel), T.V_pct(sel), '-', 'Color',[0.17 0.42 0.69], 'LineWidth',1.2);
ylabel('覆盖度 / %'); legend({'未质控','质控+派生'}, 'Location','northwest');
title('于田站：预处理后的覆盖度与水分状态'); grid on;
subplot(2,1,2);
plot(T.date(sel), T.W(sel), '-', 'Color',[0.15 0.45 0.30], 'LineWidth',1.2);
ylabel('W（0—1）'); xlabel('时间'); grid on;
exportgraphics(f, OUT_FIG, 'Resolution', 150);
close(f);
fprintf('  图件：%s\n', OUT_FIG);

fprintf('\n================ 完成 ================\n');
fprintf('  %s\n  %s\n', OUT_CSV, OUT_FIG);

%% ========== 局部函数 ====================================================
function et0 = hargreaves(T)
%HARGREAVES 由气温与天文辐射计算参考蒸散（mm/月），含 0.408 单位换算
    LAT = containers.Map( ...
        {'YT','MF','QM','RQ','KEL','YL','ALE','XT','TZ'}, ...
        [36.85 37.06 38.13 39.02 41.76 41.34 40.55 38.83 38.97]);
    et0 = nan(height(T),1);
    for i = 1:height(T)
        lat = LAT(char(T.site(i)));
        d0  = day(datetime(T.date(i).Year, T.date(i).Month, 1), 'dayofyear');
        doy = d0 + (0:T.days_in_month(i)-1);
        Ra  = ra_fao(lat, doy);
        tr  = T.T2M_MAX(i) - T.T2M_MIN(i);
        if ~isnan(tr) && tr > 0
            et0(i) = 0.0023 * 0.408 * mean(Ra) * (T.T2M(i) + 17.8) * sqrt(tr) * T.days_in_month(i);
        end
    end
end

function Ra = ra_fao(lat, doy)
%RA_FAO FAO-56 天文辐射，MJ m-2 d-1
    phi   = deg2rad(lat);
    dr    = 1 + 0.033*cos(2*pi*doy/365);
    delta = 0.409*sin(2*pi*doy/365 - 1.39);
    ws    = acos(min(max(-tan(phi)*tan(delta), -1), 1));
    Ra    = (24*60/pi)*0.0820*dr .* (ws.*sin(phi).*sin(delta) + cos(phi).*cos(delta).*sin(ws));
end

