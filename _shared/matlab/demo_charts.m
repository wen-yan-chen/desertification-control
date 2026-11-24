function demo_charts(out, palette)
%DEMO_CHARTS Every chart type in charts/ on synthetic data, one figure each.
%   Run from this folder:  matlab -batch demo_charts
%   demo_charts(out, palette) writes <function name>.png to out (default
%   ../gallery/charts) in the given palette (default 'oasis').
%   Each block is the shortest call that gives a finished figure: copy it,
%   swap in your data, and keep the axis labels.
here = fileparts(mfilename('fullpath'));
addpath(here, fullfile(here, 'charts'));
if nargin < 1 || isempty(out), out = fullfile(here, '..', 'gallery', 'charts'); end
if nargin < 2, palette = 'oasis'; end
S = paper_style('out', out, 'palette', palette); S.pdf = false; S.dpi = 220; c = S.c;
rng(7);

% ---------------------------------------------------------------- compare
[fig, ax] = one(9, 6.2);
grouped_bars(ax, [42 55 61; 38 47 58; 30 44 49; 25 31 46], {'North', 'East', 'South', 'West'}, S, ...
    'names', {'2024', '2025', '2026'}, 'colors', [c.waterLight * 0.9; c.waterMid; c.water]);
ylabel(ax, 'Treated area (ha)');
done(fig, ax, 'grouped_bars', S, 'frame');

[fig, ax] = one(9.5, 6.2);
stacked_bars(ax, [22 34 44; 40 60 0; 30 45 25; 18 52 30; 20 30 50], ...
    {'Base', 'No PV', 'Low tariff', 'High upkeep', 'Cheap PV'}, S, ...
    'names', {'Build', 'O&M', 'PV'}, 'colors', [c.vegMid; c.plum; c.accent]);
xlabel(ax, 'Share of spending (%)');
done(fig, ax, 'stacked_bars', S, 'frame');

[fig, ax] = one(10, 6.2);
waterfall_bars(ax, 25.3, [2.5 -4.1 3.7 -5.0 1.2], {'Base', 'Tariff', 'Capex', 'O&M', 'Cover', 'Water', 'Final'}, S);
ylabel(ax, 'Net cost (M CNY)');
done(fig, ax, 'waterfall_bars', S, 'frame');

[fig, ax] = one(9, 6.2);
dumbbell_rows(ax, [12 18 9 22 15 7], [21 24 19 25 26 9], {'Site A', 'Site B', 'Site C', 'Site D', 'Site E', 'Site F'}, S, ...
    'names', {'2015', '2025'});
xlabel(ax, 'Cover (%)');
done(fig, ax, 'dumbbell_rows', S, 'frame');

[fig, ax] = one(9.5, 6.2);
tornado_bars(ax, [14.2 16.1 16.9 17.2 17.6 17.8], [20.9 19.4 18.8 18.5 18.1 17.9], 17.9, ...
    {'Demand coeff.', 'Irrigation eff.', 'Rain share', 'Cover scale', 'Capacity', 'Stress point'}, S);
xlabel(ax, 'Long-run cover (%)');
done(fig, ax, 'tornado_bars', S, 'frame');

[fig, ax] = one(9.5, 6.2);
lollipop_rows(ax, [7.1 7.5 6.5 8.1 9.4 4.4], ["Baseline", "Stable climate", "Water 80%", "Water 120%", ...
    "Early shocks", "Strict threshold"], 7.1, S, 'highlight', 1, 'xlim', [3 11], ...
    'colors', [c.plum; c.plum; c.water; c.water; c.plum; c.pvDark]);
xlabel(ax, 'Time to warning (yr)');
done(fig, ax, 'lollipop_rows', S, 'frame');

% ----------------------------------------------------------------- spread
[fig, ax] = one(9.5, 6.6);
est = [-0.85 -0.80; -0.25 -0.22; -0.03 -0.02; -0.55 -0.45; -1.05 -0.50; 0.10 0.05];
interval_rows(ax, est, [-1.1 -0.5 -0.1 -1.2 -0.9 -0.3], [1.1 0.25 0.05 1.0 0.7 0.4], ...
    {'A, yr 10', 'A, yr 30', 'A, yr 50', 'B, yr 10', 'B, yr 30', 'B, yr 50'}, S, ...
    'names', {'95% interval', 'coarse grid', 'fine grid'}, 'ncol', 3);
xlabel(ax, 'Difference from reference (pp)');
done(fig, ax, 'interval_rows', S, 'frame');

[fig, ax] = one(9.5, 6.6);
raincloud_rows(ax, {10 + 2 * randn(90, 1), 13.5 + 3 * randn(90, 1), [7 + randn(55, 1); 12 + 1.2 * randn(35, 1)]}, ...
    {'Plan A', 'Plan B', 'Plan C'}, S, 'colors', [c.water; c.accent; c.veg]);
xlabel(ax, 'Time to warning (yr)');
done(fig, ax, 'raincloud_rows', S, 'frame');

[fig, ax] = one(9, 7);
x = linspace(0, 24, 160)'; mu = [13 13.5 14 14.6 15 14.2]; sg = [2.2 2.6 3 3.3 3.1 2.5];
Y = exp(-0.5 * ((x - mu) ./ sg) .^ 2) ./ sg + 0.12 * exp(-0.5 * ((x - 6) / 1.3) .^ 2);
ridge_lines(ax, x, Y, {'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep'}, S);
xticks(ax, 0:6:24); xlabel(ax, 'Hour of day');
done(fig, ax, 'ridge_lines', S, 'frame');

[fig, ax] = one(9.5, 6.2);
t = (0:50)'; Y = [9 + 14 * exp(-t / 16), 7 + 10 * exp(-t / 11), 2 + 13 * exp(-t / 7)];
band_lines(ax, t, Y, S, 'lo', Y - [2.5 2 1.2] .* (1 + t / 60), 'hi', Y + [2.5 2 1.2] .* (1 + t / 60), ...
    'names', {'600 mm/yr', '300 mm/yr', 'Rain only'}, 'colors', [c.water; c.veg; c.sand]);
xticks(ax, 0:10:50); xlabel(ax, 'Year'); ylabel(ax, 'Cover (%)');
done(fig, ax, 'band_lines', S, 'frame');

[fig, ax] = one(10, 6.6);
Z = round(min(100, [12 20 31 44 52 60 66 70] .* [0.55; 0.95; 1.36; 1.30; 1.12; 0.7])); Z(1, 1:2) = NaN;
heatmap_grid(ax, Z, S, 'xlabels', string(1:8), 'ylabels', {'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep'}, ...
    'clim', [0 100], 'cbar', 'Cap used (%)', 'mark', [3 8]);
xlabel(ax, 'Project year');
done(fig, ax, 'heatmap_grid', S, 'frame');

[fig, ax] = one(9, 6.8);
R = [1 .62 -.41 .18 -.55; .62 1 -.22 .35 -.30; -.41 -.22 1 -.08 .71; .18 .35 -.08 1 .12; -.55 -.30 .71 .12 1];
heatmap_grid(ax, R, S, 'xlabels', {'V', 'M', 'E', 'T', 'S'}, 'ylabels', {'V', 'M', 'E', 'T', 'S'}, ...
    'clim', [-1 1], 'cmap', 'div', 'fmt', '%.2f', 'cbar', 'Correlation');
done(fig, ax, 'heatmap_grid_div', S, 'frame');

% -------------------------------------------------------------- structure
[fig, ax] = one(9, 8, 'loose');
radar_chart(ax, [0.82 0.55 0.70 0.38 0.90 0.62; 0.48 0.85 0.52 0.74 0.45 0.80], ...
    {'Cover', 'Water use', 'Cost', 'Labour', 'Resilience', 'Income'}, S, 'names', {'Plan A', 'Plan B'});
done(fig, ax, 'radar_chart', S, 'equal');

[fig, ax] = one(10.5, 6);
donut_share(ax, [44 22 18 10 6], {'PV capital', 'Planting', 'Upkeep', 'Water', 'Other'}, S, ...
    'colors', [c.accent; c.vegMid; c.plum; c.water; c.grey], 'center', {'80 M', 'CNY'});
done(fig, ax, 'donut_share', S, 'equal');

[fig, ax] = one(10, 6.8);
alluvial_flow(ax, [60 25 5; 20 45 15; 5 20 55], {'Canal', 'Wells', 'Rain'}, {'Belt', 'Farms', 'Losses'}, S, ...
    'colors', [c.water; c.teal; c.waterMid]);
done(fig, ax, 'alluvial_flow', S, 'none');

[fig, ax] = one(9, 7.5);
A = zeros(9); e = [1 2 5; 2 3 4; 3 4 3; 4 5 4; 5 6 5; 6 7 3; 7 1 2; 8 1 1; 8 2 3; 8 7 2; 8 9 5; 9 3 2; 9 5 3; 9 6 1];
for k = 1:size(e, 1), A(e(k, 1), e(k, 2)) = e(k, 3); end
xy = [0 0; 1.3 -0.4; 2.6 0.1; 3.5 1.1; 3.0 2.4; 1.8 2.9; 0.4 2.2; 1.2 1.1; 2.3 1.5];
network_graph(ax, A, S, 'xy', xy, 'labels', {'YT', 'MF', 'QM', 'RQ', 'KEL', 'YL', 'ALE', 'XT', 'TZ'}, ...
    'groups', [1 1 1 1 2 2 2 3 3], 'colors', [c.water; c.accent; c.plum]);
done(fig, ax, 'network_graph', S, 'equal');

[fig, ax] = one(10, 6.4);
bump_ranks(ax, [1 1 2 3 3; 2 3 1 1 1; 3 2 3 2 4; 4 5 5 4 2; 5 4 4 6 6; 6 6 6 5 5], ...
    {'Plan A', 'Plan B', 'Plan C', 'Plan D', 'Plan E', 'Plan F'}, S, 'highlight', [2 4 1], ...
    'xlabels', {'20%', '40%', '60%', '80%', '100%'}, 'colors', [c.water; c.accent; c.plum], 'room', 1.0);
xlabel(ax, 'Ecological target'); ylabel(ax, 'Cost rank');
done(fig, ax, 'bump_ranks', S, 'frame');

[fig, ax] = one(10.5, 6.4);
gantt_rows(ax, [0 0 1 2 2 4 5], [2 1 4 5 6 9 15], {'Survey', 'Canal', 'Plant lot 1', 'Plant lot 2', 'PV build', ...
    'Ramp water', 'Upkeep'}, S, 'groups', [1 1 2 2 3 2 2], 'colors', [c.sand; c.vegMid; c.accent], ...
    'names', {'Prepare', 'Belt', 'PV'}, 'deadline', 12, 'deadlinelabel', 'audit');
xlabel(ax, 'Project year');
done(fig, ax, 'gantt_rows', S, 'frame');

% ------------------------------------------------------------------ model
[fig, ax] = one(9.5, 6.6);
u = rand(160, 1); cost = 8 + 50 * u + 6 * randn(160, 1); ben = 400 + 1700 * sqrt(u) - 260 * rand(160, 1) .^ 0.6;
front = pareto_scatter(ax, cost, ben, S, 'maximize', [false true]); cla(ax);
pareto_scatter(ax, cost, ben, S, 'maximize', [false true], 'pick', front(ceil(end / 2)), 'picklabel', 'chosen plan');
xlabel(ax, 'Net cost (M CNY)'); ylabel(ax, 'Benefit (effective ha\cdotyr)');
done(fig, ax, 'pareto_scatter', S, 'frame');

[fig, ax] = one(9, 6.8);
feasible_region(ax, [1 1; 2 1; 0 1], [8; 12; 5], [0 7], [0 8.5], S, ...
    'names', {'budget', 'water', 'labour'}, 'objective', [3 2]);
xlabel(ax, 'Belt area {\itx}'); ylabel(ax, 'PV capacity {\ity}');
done(fig, ax, 'feasible_region', S, 'frame');

[fig, ax] = one(9.5, 6.2);
x = linspace(0, 15, 61)';
break_even(ax, x, 10 + 0.9 * x, 2.1 * x, S, 'fmt', 'break-even, year %.1f', 'room', 0.25);
xticks(ax, 0:5:15); xlabel(ax, 'Project year'); ylabel(ax, 'Cumulative (M CNY)');
done(fig, ax, 'break_even', S, 'frame');

[fig, ax] = one(10, 6.6);
[X, Y] = meshgrid(linspace(0, 1000, 60), linspace(0, 12, 60));
Z = 30 * (1 - exp(-X / 260)) .* exp(-((Y - 7.5) / 5.5) .^ 2) - 0.008 * X;
[~, k] = max(Z(:));
contour_field(ax, X, Y, Z, S, 'levels', 0:3:21, 'mark', [X(k) Y(k)], 'cbar', 'Net benefit (M CNY)');
xlabel(ax, 'Irrigation (mm/yr)'); ylabel(ax, 'PV capacity (MW)');
done(fig, ax, 'contour_field', S, 'frame');

[fig, ax] = one(10, 7.6, 'loose');
i = 1:3:60;
surface3d(ax, X(i, i), Y(i, i), Z(i, i), S, 'mark', [X(k) Y(k) Z(k)]);
xlabel(ax, 'Irrigation (mm/yr)'); ylabel(ax, 'PV (MW)'); zlabel(ax, 'Net benefit (M CNY)');
done(fig, ax, 'surface3d', S, 'none');

[fig, ax] = one(9, 7);
f = @(z) [z(1) * (1 - z(1) / 3) - 0.8 * z(1) * z(2); -0.5 * z(2) + 0.6 * z(1) * z(2)];
phase_portrait(ax, f, [0 3.2], [0 2], S, 'starts', [2.8 0.25; 0.3 1.7; 1.6 1.85], ...
    'equilibria', [0.5 / 0.6, (1 - 0.5 / 0.6 / 3) / 0.8; 3 0]);
xlabel(ax, 'Vegetation {\itV}'); ylabel(ax, 'Grazing pressure {\itG}');
done(fig, ax, 'phase_portrait', S, 'frame');

% ------------------------------------------------------------------- time
[fig, ax] = one(9.5, 6.2);
t = (1:15)'; Y = [8 * exp(-t / 3) + 0.3, 1.2 + 0.25 * t .* exp(-t / 9), 5 * exp(-((t - 3) / 1.6) .^ 2), 0.9 + 0 * t];
stacked_area(ax, t, Y, S, 'names', {'Planting', 'Upkeep', 'PV', 'Water'}, 'colors', [c.vegMid; c.plum; c.accent; c.water]);
xlabel(ax, 'Project year'); ylabel(ax, 'Spending (M CNY)');
done(fig, ax, 'stacked_area', S, 'frame');

[fig, ax] = one(9.5, 6.2);
x = linspace(0, 24, 97)';
Y = [1.5 + sin(x / 4) .^ 2, 1 + 2 * exp(-((x - 13) / 4) .^ 2), 0.6 + 0.9 * exp(-((x - 19) / 2.5) .^ 2), 0.8 + 0.5 * cos(x / 5) .^ 2];
stacked_area(ax, x, Y, S, 'stream', true, 'names', {'Canal', 'Wells', 'Reuse', 'Rain'}, ...
    'colors', [c.water; c.teal; c.waterMid; c.waterLight * 0.9]);
xticks(ax, 0:6:24); xlabel(ax, 'Month');
done(fig, ax, 'stacked_area_stream', S, 'frame');

[fig, ax] = one(10, 7.6, 'loose');
Z = [8.8 3.7 2.8; 20.7 7.3 5.2; 41.8 16.6 11.4];
bars3d(ax, Z, S, 'labels', arrayfun(@(z) sprintf('\\bf%.1f', z), Z, 'UniformOutput', false), ...
    'clim', [2.5 42.5], 'highlight', [2 2], 'zmax', 52);
xticklabels(ax, {'0.15', '0.30', '0.45'}); yticklabels(ax, {'0.50', '0.25', '0.10'}); zticks(ax, 0:10:50);
xlabel(ax, 'Mean loss per storm'); ylabel(ax, 'Storm rate (yr^{-1})'); zlabel(ax, 'Time to warning (yr)');
done(fig, ax, 'bars3d', S, 'none');
end

function [fig, ax] = one(w, h, pad)
% One chart on its own canvas (cm); the layout keeps room for the labels.
if nargin < 3, pad = 'compact'; end
fig = new_figure(w, h);
tl = tiledlayout(fig, 1, 1, 'Padding', pad);
ax = nexttile(tl);
end

function done(fig, ax, name, S, mode)
% 'frame' closes the axes box, 'equal' fills the slot of an equal-aspect chart.
switch mode
    case 'frame', frame_axes(ax, S);
    case 'equal', fit_equal(ax);
end
save_fig(fig, name, S);
end
