function fig_m3_sensitivity_val()
%FIG_M3_SENSITIVITY_VAL Paper Fig. "Compound-hazard sensitivity".
%   (a) Discrete 3x3 frequency-severity grid (RMST(50) + 50-yr hit rate),
%   (b) Post-construction mechanism & rationing contrasts (no M1 overlap),
%   Data: Results/v7/model3/{summary.csv, project_annual.csv, markov_mc_comparison.csv, validation_summary.json}
S = paper_style(); c = S.c;
check_m3_hashes(S);
sm = readtable(fullfile(S.res3, 'summary.csv'), 'TextType', 'string', 'VariableNamingRule', 'preserve');
pa = readtable(fullfile(S.res3, 'project_annual.csv'), 'TextType', 'string', 'VariableNamingRule', 'preserve');

fig = new_figure(S.textW, 6.8);

% ==================== (a) 3D bar chart: 3x3 joint hazard grid ====================
ax1 = axes(fig, 'Position', [0.052 0.12 0.422 0.76]);
style_axes(ax1, S, 'xy');
set(ax1, 'ZGrid', 'on', 'ZColor', c.axis, 'ZMinorTick', 'off', ...
    'TickDir', 'out', 'Projection', 'orthographic', 'Box', 'off', ...
    'TickLength', [0.015 0.015]);
ax1.ZLabel.FontSize = S.fs.label;
ax1.ZLabel.Color = c.ink;

lamStr = ["0.1", "0.25", "0.5"];
muStr  = ["0.15", "0.3", "0.45"];

% Custom 64-step colormap from warm sand/coral (short RMST) to deep oasis teal (long RMST)
anchors = [c.limit; c.accent; c.sandLight; c.vegMid; c.water];
cmap = interp1(linspace(0, 1, size(anchors, 1)), anchors, linspace(0, 1, 64));

az = 28; el = 32;
camXY = [sind(az), -cosd(az)];

% Collect all 9 grid entries and sort back-to-front along camera axis
bars = struct('x', {}, 'y', {}, 'rmst', {}, 'p50', {}, 'isBase', {}, 'depth', {});
k = 0;
for ir = 1:3       % lambda_0: 0.10 -> y=3 (back), 0.25 -> y=2, 0.50 -> y=1 (front)
    for ic = 1:3   % E[U]:     0.15 -> x=1 (left), 0.30 -> x=2, 0.45 -> x=3 (right)
        cname = "joint_rate_" + lamStr(ir) + "_loss_" + muStr(ic);
        row = sm(sm.("case") == cname & sm.entity == "project", :);
        k = k + 1;
        x0 = ic;
        y0 = 4 - ir;
        bars(k).x      = x0;
        bars(k).y      = y0;
        bars(k).rmst   = row.restricted_mean_first_passage_years;
        bars(k).p50    = row.p_failure * 100;
        bars(k).isBase = (ir == 2 && ic == 2);
        bars(k).depth  = x0 * camXY(1) + y0 * camXY(2);
    end
end
[~, ord] = sort([bars.depth], 'ascend');
bars = bars(ord);

w = 0.21;
for b = 1:numel(bars)
    x0   = bars(b).x;
    y0   = bars(b).y;
    h    = bars(b).rmst;
    frac = min(1, max(0, (h - 2.5) / (42.5 - 2.5)));
    idx  = max(1, min(64, round(1 + frac * 63)));
    fcol = cmap(idx, :);

    colTop   = min(1, fcol * 1.04 + 0.05);
    colFront = fcol * 0.92;
    colSide  = fcol * 0.76;
    ecol     = 0.55 * fcol + 0.45 * c.axis;
    lw       = 0.42;
    if bars(b).isBase
        ecol = c.ink;
        lw   = 0.65;
    end

    % Front-left face (y = y0 - w)
    patch(ax1, [x0-w x0+w x0+w x0-w], [y0-w y0-w y0-w y0-w], [0 0 h h], colFront, ...
        'EdgeColor', ecol, 'LineWidth', lw, 'HandleVisibility', 'off');
    % Front-right face (x = x0 + w)
    patch(ax1, [x0+w x0+w x0+w x0+w], [y0-w y0+w y0+w y0-w], [0 0 h h], colSide, ...
        'EdgeColor', ecol, 'LineWidth', lw, 'HandleVisibility', 'off');
    % Top face (z = h)
    patch(ax1, [x0-w x0+w x0+w x0-w], [y0-w y0-w y0+w y0+w], [h h h h], colTop, ...
        'EdgeColor', ecol, 'LineWidth', lw, 'HandleVisibility', 'off');
end

% Draw labels in a second pass so they always render crisply in front of bars
for b = 1:numel(bars)
    x0   = bars(b).x;
    y0   = bars(b).y;
    h    = bars(b).rmst;
    p50  = bars(b).p50;
    dx = 0; dy = 0; dz = 2.7;
    if x0 == 1 && y0 == 2, dx = -0.14; dz = 2.7; end   % 20.7 yr: clear 41.8 bar
    if x0 == 2 && y0 == 1, dx = -0.10; dz = 2.3; end   %  3.7 yr: clear 7.3* bar
    if x0 == 3 && y0 == 1, dx = -0.06; dz = 2.1; end   %  2.8 yr: clear 5.2 bar
    if x0 == 3 && y0 == 2, dx = -0.05; dz = 2.4; end   %  5.2 yr: clear 11.4 bar
    if x0 == 2 && y0 == 2, dx =  0.05; dz = 2.4; end   %  7.3 yr*: centered in corridor
    star = "";
    if bars(b).isBase, star = "*"; end
    lbl = {sprintf('\\bf%.1f yr%s', h, star), ...
           sprintf('\\rm\\fontsize{%.1f}(%.1f%%)', S.fs.note - 1.6, p50)};
    text(ax1, x0 + dx, y0 + dy, h + dz, lbl, ...
        'FontName', S.font, 'FontSize', S.fs.note - 1.1, 'Color', c.ink, ...
        'HorizontalAlignment', 'center', 'VerticalAlignment', 'bottom', ...
        'Interpreter', 'tex');
end

xlim(ax1, [0.45 3.55]); ylim(ax1, [0.45 3.55]); zlim(ax1, [0 52]);
xticks(ax1, 1:3); xticklabels(ax1, {'0.15', '0.30', '0.45'});
yticks(ax1, 1:3); yticklabels(ax1, {'0.50', '0.25', '0.10'});
zticks(ax1, 0:10:50);
xlh = xlabel(ax1, 'Mean event loss E[{\itU}]');
ylh = ylabel(ax1, {'Initial storm rate', '\lambda_0 (yr^{-1})'});
zlabel(ax1, 'RMST(50) (yr)');
pbaspect(ax1, [1.22 1.15 0.88]);
view(ax1, az, el);
set(xlh, 'Rotation', -17, 'VerticalAlignment', 'top', 'Position', [1.95 0.08 -4.0]);
set(ylh, 'Rotation',  41, 'VerticalAlignment', 'top', 'HorizontalAlignment', 'center', ...
    'Position', [4.02 2.15 -3.6]);
t1 = panel_title(ax1, '(a) Joint grid: RMST(50) & ({\itp}_{50})', S);
t1.Units = 'normalized';
t1.Position(2) = 1.022;

% ==================== (b) Post-construction mechanism & rationing contrasts ====================
ax = axes(fig, 'Position', [0.635 0.14 0.350 0.78]); style_axes(ax, S, 'x');
cases = ["base_nonstationary", "stationary_reference", "water_80pct", "water_120pct", ...
         "no_drought", "no_drought_storm_association", "independent_cohort_storms", ...
         "fixed_mean_loss", "storm_at_year_start", "threshold_20pctK", "threshold_40pctK"];
labs  = ["Base (non-stationary)", "Stationary climate", "Water request 80%", ...
         "Water request 120%", "No drought shocks", "No dry–storm link (\gamma=1)", ...
         "Indep. cohort storms", "Fixed loss {\itU} = 0.30", "Start-year shocks", ...
         "Threshold 0.20{\itK} (diag.)", "Threshold 0.40{\itK} (diag.)"];
n = numel(cases);
labs(1) = sprintf('\\color[rgb]{%.3f,%.3f,%.3f}\\bfBase (non-stationary)', c.water);
yv = (n:-1:1)';
baseR = sm.restricted_mean_first_passage_years(sm.("case") == "base_nonstationary" & sm.entity == "project");

for r = 2:2:n
    patch(ax, [1.0 20.8 20.8 1.0], r + [-0.5 -0.5 0.5 0.5], c.grid, ...
        'EdgeColor', 'none', 'FaceAlpha', 0.55, 'HandleVisibility', 'off');
end
% Highlight the baseline row
patch(ax, [1.0 20.8 20.8 1.0], n + [-0.5 -0.5 0.5 0.5], c.waterLight, ...
    'EdgeColor', 'none', 'FaceAlpha', 0.9, 'HandleVisibility', 'off');
xline(ax, baseR, '--', 'Color', c.greyDark, 'LineWidth', 0.85, 'HandleVisibility', 'off');
yline(ax, 2.5, ':', 'Color', c.limit, 'LineWidth', 0.8, 'HandleVisibility', 'off');

for k = 1:n
    rk = sm.restricted_mean_first_passage_years(sm.("case") == cases(k) & sm.entity == "project");
    col = c.plum;
    if contains(cases(k), "water"), col = c.water; end
    if contains(cases(k), "threshold"), col = c.pvDark; end
    plot(ax, [baseR rk], [yv(k) yv(k)], '-', 'Color', c.grey, 'LineWidth', 1.25, 'HandleVisibility', 'off');
    plot(ax, rk, yv(k), 'o', 'MarkerSize', 4.0, 'MarkerFaceColor', col, ...
        'MarkerEdgeColor', 'w', 'LineWidth', 0.45, 'HandleVisibility', 'off');
    dx = 0.50; ha = 'left';
    if rk < baseR - 0.15, dx = -0.50; ha = 'right'; end
    text(ax, rk + dx, yv(k), sprintf('%.1f', rk), ...
        'FontName', S.font, 'FontSize', S.fs.note - 0.5, 'Color', c.ink, 'HorizontalAlignment', ha);
end
xlim(ax, [1.0 20.8]); xticks(ax, 5:5:20);
ylim(ax, [0.4 n + 0.6]); yticks(ax, 1:n); yticklabels(ax, flip(labs));
ax.YAxis.TickLength = [0 0]; ax.YAxis.FontSize = S.fs.note - 0.5;
xlabel(ax, 'Project RMST(50) (yr)');
panel_title(ax, '(b) Mechanism contrasts', S);
frame_axes(ax, S);

save_fig(fig, 'm3_sensitivity_val', S);
end
