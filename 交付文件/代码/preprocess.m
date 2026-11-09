%% preprocess.m —— 《治沙是一项精细活》B 题：数据预处理（MATLAB 版）
%  与 preprocess.py 步骤一一对应：读取→规范化→去重→单位统一→物理阈值→
%  异常值→缺失插补（含结构性缺失修复）→面板对齐→特征工程→共线性→标准化→划分
%
%  运行环境：MATLAB R2020b 及以上（仅用内置函数，无需工具箱）
%  用法：直接运行本脚本（F5）。若数据路径不同，只改下面 PATH 段。
% ----------------------------------------------------------------------
clear; clc; close all;

%% ======================= 路径设置（按需修改） =========================
% Windows 示例： BASE = 'D:\CQU\大三上\比赛\美赛\第一次校赛\交付文件';
% macOS/Linux：  BASE = '/Users/xxx/project/交付文件';
BASE   = fileparts(fileparts(mfilename('fullpath')));   % 上一级 = 交付文件/
RAW    = fullfile(BASE, '数据', 'raw', '02_站点月尺度面板_raw.csv');
OUTD   = fullfile(BASE, '数据', 'processed');
FIGD   = fullfile(BASE, '图');
if ~exist(OUTD, 'dir'), mkdir(OUTD); end
if ~exist(FIGD, 'dir'), mkdir(FIGD); end
% ======================================================================

%% 1. 读取数据（含异常处理）
if ~isfile(RAW)
    error('【读取失败】找不到文件：%s\n→ 请检查路径拼写、盘符，以及文件是否在 数据/raw/ 下。', RAW);
end
opts = detectImportOptions(RAW, 'Encoding', 'UTF-8');
opts.VariableNamingRule = 'preserve';
T = readtable(RAW, opts);
if iscellstr(T.站点)  %#ok<ISCLSTR>  % 兼容旧版本
    T.站点 = string(T.站点);
end
fprintf('原始数据：%d 行 × %d 列\n', height(T), width(T));

%% 2. 规范化：时间、站点名、地表类型、数值文本
n = height(T);
mo = NaT(n, 1);
for i = 1:n
    s = strtrim(string(T.月份(i)));
    s = replace(s, '年', '-'); s = replace(s, '月', '');
    s = replace(s, '/', '-');
    parts = split(s, '-');
    if numel(parts) >= 2
        mo(i) = datetime(str2double(parts(1)), str2double(parts(2)), 1);
    end
end
T.月份 = mo;
T.month     = month(T.月份);
T.monthIdx  = (year(T.月份) - 2015) * 12 + month(T.月份) - 1;

T.站点 = strtrim(T.站点);
mapSta = {"塔中站","塔中"; "TZ","塔中"; "XT","肖塘"; "QM","且末"; "MF","民丰";
          "RQ","若羌"; "KEL","库尔勒"; "YL","尉犁"; "ALE","阿拉尔"};
for i = 1:size(mapSta, 1)
    T.站点(T.站点 == mapSta{i, 1}) = mapSta{i, 2};
end

mapSurf = {"mobile dune","流动沙丘"; "semi-fixed sandy land","半固定沙地";
           "gobi","戈壁"; "oasis-desert ecotone","绿洲—荒漠过渡带";
           "oasis fringe","绿洲边缘"; "oasis-desert interlaced zone","绿洲—沙漠交错带"};
T.地表类型 = lower(strtrim(string(T.地表类型)));
for i = 1:size(mapSurf, 1)
    T.地表类型(T.地表类型 == mapSurf{i, 1}) = mapSurf{i, 2};
end

numVars = ["风速","降水","气温","土壤含水率","植被覆盖度","输沙率"];
for v = numVars
    if iscell(T.(v)) || isstring(T.(v))
        s = string(T.(v));
        s = regexprep(s, '[^0-9\.\-]', '');          % 去掉 "3.2 m/s" 之类的单位后缀
        T.(v) = str2double(s);
    else
        T.(v) = double(T.(v));
    end
end

%% 3. 去重（完全重复 + 站-月键重复）
n0 = height(T);
[~, ia] = unique(T(:, {'站代码','月份'}), 'rows', 'stable');
T = T(sort(ia), :);
fprintf('去重：%d → %d 行\n', n0, height(T));

%% 4. 单位统一
fac = ones(height(T), 1);
u = strtrim(string(T.风速_单位));
T.风速 = T.风速 .* fac;
T.风速(u == "km/h") = T.风速(u == "km/h") / 3.6;

p = strtrim(string(T.降水_单位));
T.降水(p == "cm") = T.降水(p == "cm") * 10;

q = strtrim(string(T.输沙率_单位));
T.输沙率(q == "g/(cm·min)") = T.输沙率(q == "g/(cm·min)") * 525.6;
fprintf('单位换算：km/h %d 行，cm %d 行，g/(cm·min) %d 行\n', ...
    sum(u == "km/h"), sum(p == "cm"), sum(q == "g/(cm·min)"));

%% 5. 物理阈值（不可能值 → NaN）
lo = [0 0 -45 0.2 0 0];  hi = [40 400 50 25 100 5000];
for k = 1:numel(numVars)
    v = numVars(k); x = T.(v);
    x(x < lo(k) | x > hi(k)) = NaN;
    T.(v) = x;
end

%% 6. 异常值检测（IQR / MAD / 时序残差）
fprintf('\n--- 异常值检测（IQR + MAD）---\n');
for v = ["风速","降水","土壤含水率","植被覆盖度","输沙率"]
    x = T.(v)(~isnan(T.(v)));
    q1 = PCTILE(x, 25); q3 = PCTILE(x, 75); iqr_ = q3 - q1;
    m1 = (T.(v) < q1 - 1.5 * iqr_) | (T.(v) > q3 + 1.5 * iqr_);       % IQR 准则
    med = median(x); mad_ = median(abs(x - med));                     % 稳健 Z 准则
    m2 = abs(T.(v) - med) > 3.5 * 1.4826 * mad_;
    fprintf('%-8s IQR=%3d  MAD=%3d  合计=%3d (%.1f%%)\n', v, sum(m1), sum(m2), ...
        sum(m1 | m2), 100 * sum(m1 | m2) / numel(x));
end

%% 7. 缺失插补（按站点线性插值 + 同月气候态兜底）
stations = unique(T.站代码);
for s = 1:numel(stations)
    idx = find(T.站代码 == stations(s));
    [~, o] = sort(T.月份(idx));
    idx = idx(o);
    for v = ["风速","降水","气温","土壤含水率","植被覆盖度"]
        x = T.(v)(idx);
        x = fillmissing(x, 'linear', 'EndValues', 'nearest');   % 线性插值
        T.(v)(idx) = x;
    end
end
% 同月气候态兜底（跨年同月均值）
for v = ["风速","降水","气温","土壤含水率","植被覆盖度"]
    x = T.(v);
    for s = 1:numel(stations)
        for m = 1:12
            msk = (T.站代码 == stations(s)) & (T.month == m);
            mu = mean(x(msk), 'omitnan');
            x(msk & isnan(x)) = mu;
        end
    end
    T.(v) = x;
end

%% 7b. 结构性缺失修复（若羌 2023 全年风速传感器故障）
yearFix = 2023; staFix = "RQ"; v = "风速";
maskFix = (T.站代码 == staFix) & (year(T.月份) == yearFix) & ISNAN_COL(T, v);
if any(maskFix)
    for m = 1:12
        base = mean(T.(v)((T.站代码 == staFix) & (T.month == m) & (year(T.月份) < yearFix)), 'omitnan');
        rNow = mean(T.(v)((T.month == m) & (year(T.月份) == yearFix)), 'omitnan');
        rRef = mean(T.(v)((T.month == m) & (year(T.月份) < yearFix)), 'omitnan');
        ratio = rNow / rRef;
        sel = maskFix & (T.month == m);
        if any(sel) && ~isnan(base) && ~isnan(ratio)
            T.(v)(sel) = base * ratio;
        end
    end
    fprintf('结构性缺失修复：%s站 %d 年 %s 共 %d 个月\n', staFix, yearFix, v, sum(maskFix));
end

%% 8. 面板对齐（站 × 月 完整网格）
grid = table();
for s = 1:numel(stations)
    for y = 2015:2024
        for m = 1:12
            grid = [grid; table(stations(s), datetime(y, m, 1), ...
                'VariableNames', {'站代码','月份'})]; %#ok<AGROW>
        end
    end
end
T = outerjoin(grid, T, 'Keys', {'站代码','月份'}, 'MergeKeys', true, ...
    'Type', 'left');
T.month = month(T.月份);
T.monthIdx = (year(T.月份) - 2015) * 12 + month(T.月份) - 1;

%% 9. 特征工程
T.月份_sin  = sin(2 * pi * T.month / 12);
T.月份_cos  = cos(2 * pi * T.month / 12);
T.干燥度    = T.降水 ./ max(T.气温 + 10, 1);
T.风蚀动力  = T.风速 .^ 3;
T.水分抑制  = exp(-0.22 * T.土壤含水率);
T.覆盖抑制  = exp(-0.075 * T.植被覆盖度);
T.log治理面积 = log1p(T.累计治理面积);
T.治理年限  = T.monthIdx / 12;
if ~ismember('log输沙率', T.Properties.VariableNames)
    T.log输沙率 = log1p(T.输沙率);
end

%% 10. 共线性 VIF（阈值 10）
feats = ["风速","降水","气温","土壤含水率","植被覆盖度","干燥度", ...
         "月份_sin","月份_cos","log治理面积","治理年限"];
X = T{:, cellstr(feats)};
X = X(~any(isnan(X), 2), :);
fprintf('\n--- VIF ---\n');
for j = 1:numel(feats)
    y = X(:, j);
    A = [ones(size(X, 1), 1), X(:, setdiff(1:size(X, 2), j))];
    b = A \ y;
    r2 = 1 - sum((y - A * b).^2) / sum((y - mean(y)).^2);
    fprintf('%-10s VIF = %6.2f\n', feats(j), 1 / max(1 - r2, 1e-6));
end

%% 11. 标准化（稳健：中位数/IQR）与划分
trainMask = T.月份 < datetime(2023, 1, 1);
mu = median(T{trainMask, cellstr(feats)}, 1, 'omitnan');
iqr_ = PCTILE(T{trainMask, cellstr(feats)}, 75) - PCTILE(T{trainMask, cellstr(feats)}, 25);
iqr_(iqr_ == 0) = 1;
Z = (T{:, cellstr(feats)} - mu) ./ iqr_;
for j = 1:numel(feats)
    T.(char("z_" + feats(j))) = Z(:, j);
end

%% 12. 输出
keep = ["站代码","站点","月份","month","monthIdx","地表类型","风速","降水","气温", ...
        "土壤含水率","植被覆盖度","输沙率","输沙势","累计治理面积","月度投资", ...
        "生态补水","log输沙率"];
keep = keep(ismember(keep, string(T.Properties.VariableNames)));
writetable(T(:, cellstr(keep)), fullfile(OUTD, '02_panel_clean_matlab.csv'), 'Encoding', 'UTF-8');
writetable(T(trainMask, :), fullfile(OUTD, '04_train_matlab.csv'), 'Encoding', 'UTF-8');
writetable(T(~trainMask, :), fullfile(OUTD, '05_test_matlab.csv'), 'Encoding', 'UTF-8');
fprintf('\n已保存：%s\n', OUTD);

%% 13. 快速可视化（清洗前后箱线图）
figure('Position', [100 100 1100 420]);
subplot(1,4,1); boxplot(T.风速); title('风速');
subplot(1,4,2); boxplot(T.土壤含水率); title('土壤含水率');
subplot(1,4,3); boxplot(T.植被覆盖度); title('植被覆盖度');
subplot(1,4,4); boxplot(T.输沙率); title('输沙率');
saveas(gcf, fullfile(FIGD, 'fig_matlab_清洗后箱线图.png'));
fprintf('MATLAB 版流程结束。\n');

%% 辅助函数：按列计算百分位（不依赖统计工具箱，线性插值）
function q = PCTILE(x, p)
    if isvector(x), x = x(:); end
    [m, n] = size(x);
    xs = sort(x, 1);                      % 每列升序
    v = linspace(0, 1, m)';               % 经验分位位置
    q = zeros(1, n);
    for j = 1:n
        yj = xs(~isnan(xs(:, j)), j);
        if isempty(yj), q(j) = NaN; continue; end
        vj = linspace(0, 1, numel(yj))';
        q(j) = interp1(vj, yj, p / 100, 'linear', 'extrap');
    end
end

%% 辅助函数：判断某列是否为 NaN（兼容不同版本）
function m = ISNAN_COL(T, v)
    if iscell(T.(v)) || isstring(T.(v))
        m = ismissing(string(T.(v)));
    else
        m = isnan(T.(v));
    end
end
