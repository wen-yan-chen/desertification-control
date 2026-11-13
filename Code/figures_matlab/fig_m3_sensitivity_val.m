function fig_m3_sensitivity_val()
%FIG_M3_SENSITIVITY_VAL Paper Fig. "Compound-hazard sensitivity".
%   (a) Discrete 3x3 frequency-severity grid (RMST(50) + 50-yr hit rate),
%   (b) Post-construction mechanism & rationing contrasts (no M1 overlap),
%   Data: Results/v7/model3/{summary.csv, project_annual.csv, markov_mc_comparison.csv, validation_summary.json}
S = paper_style(); c = S.c;
check_m3_hashes(S);
sm = readtable(fullfile(S.res3, 'summary.csv'), 'TextType', 'string', 'VariableNamingRule', 'preserve');
pa = readtable(fullfile(S.res3, 'project_annual.csv'), 'TextType', 'string', 'VariableNamingRule', 'preserve');

fig = new_figure(S.textW, 6.2);
tl  = tiledlayout(fig, 1, 2, 'TileSpacing', 'compact', 'Padding', 'compact');

% ==================== (a) Discrete 3x3 joint hazard grid ====================
ax = nexttile(tl); style_axes(ax, S, 'none');
lams = [0.10, 0.25, 0.50];
mus  = [0.15, 0.30, 0.45];
lamStr = ["0.1", "0.25", "0.5"];
muStr  = ["0.15", "0.3", "0.45"];

% Custom 64-step colormap from warm sand/coral (short RMST) to deep oasis teal (long RMST)
anchors = [c.limit; c.accent; c.sandLight; c.vegMid; c.water];
cmap = interp1(linspace(0, 1, size(anchors, 1)), anchors, linspace(0, 1, 64));

for ir = 1:3       % row: lambda_0 (top = 0.50, bottom = 0.10)
    for ic = 1:3   % col: E[U] (left = 0.15, right = 0.45)
        cname = "joint_rate_" + lamStr(ir) + "_loss_" + muStr(ic);
        row = sm(sm.("case") == cname & sm.entity == "project", :);
        rmst = row.restricted_mean_first_passage_years;
        p50  = row.p_failure * 100;
        frac = min(1, max(0, (rmst - 2.5) / (42.5 - 2.5)));
        idx  = max(1, min(64, round(1 + frac * 63)));
        fcol = cmap(idx, :);
        patch(ax, ic + [-0.46 0.46 0.46 -0.46], ir + [-0.46 -0.46 0.46 0.46], fcol, ...
            'EdgeColor', 'w', 'LineWidth', 1.4, 'HandleVisibility', 'off');
        tcol = c.ink;
        if frac < 0.22 || frac > 0.78, tcol = [1 1 1]; end
        star = "";
        if ir == 2 && ic == 2, star = "*"; end
        text(ax, ic, ir + 0.12, sprintf('%.1f yr%s', rmst, star), ...
            'FontName', S.font, 'FontSize', S.fs.note + 0.2, 'FontWeight', 'bold', ...
            'Color', tcol, 'HorizontalAlignment', 'center');
        text(ax, ic, ir - 0.19, sprintf('(%.1f%%)', p50), ...
            'FontName', S.font, 'FontSize', S.fs.note - 0.6, ...
            'Color', tcol, 'HorizontalAlignment', 'center');
    end
end
xlim(ax, [0.5 3.5]); ylim(ax, [0.5 3.5]);
xticks(ax, 1:3); xticklabels(ax, {'0.15', '0.30', '0.45'});
yticks(ax, 1:3); yticklabels(ax, {'0.10', '0.25', '0.50'});
xlabel(ax, 'Mean event loss E[{\itU}]');
ylabel(ax, 'Initial storm rate \lambda_0 (yr^{-1})');
panel_title(ax, '(a) Joint grid: RMST(50) & ({\itp}_{50})', S);
frame_axes(ax, S);

% ==================== (b) Post-construction mechanism & rationing contrasts ====================
ax = nexttile(tl); style_axes(ax, S, 'x');
cases = ["base_nonstationary", "stationary_reference", "water_80pct", "water_120pct", ...
         "no_drought", "no_drought_storm_association", "independent_cohort_storms", ...
         "fixed_mean_loss", "storm_at_year_start", "threshold_20pctK", "threshold_40pctK"];
labs  = ["Base (non-stationary)", "Stationary climate", "Water request 80%", ...
         "Water request 120%", "No drought shocks", "No dry–storm link (\gamma=1)", ...
         "Indep. cohort storms", "Fixed loss {\itU} = 0.30", "Start-year shocks", ...
         "Threshold 0.20{\itK} (diag.)", "Threshold 0.40{\itK} (diag.)"];
n = numel(cases);
yv = (n:-1:1)';
baseR = sm.restricted_mean_first_passage_years(sm.("case") == "base_nonstationary" & sm.entity == "project");

for r = 2:2:n
    patch(ax, [1.0 20.8 20.8 1.0], r + [-0.5 -0.5 0.5 0.5], c.grid, ...
        'EdgeColor', 'none', 'FaceAlpha', 0.55, 'HandleVisibility', 'off');
end
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
