function fig_m1_water_curve()
%FIG_M1_WATER_CURVE Paper Fig. "Long-run state against irrigation".
%   (a) cover V, (b) demand met W-bar, (c) year-end store M, (d) sand exposure S.
%   Red dashed lines are limits: the water-unlimited cover K(1-d/r), W-bar = 1,
%   and the storage capacity C = 75 mm.
%   Data: Results/v7/model1/water_cover_curve.csv
S = paper_style(); c = S.c;
w = readtable(fullfile(S.res, 'water_cover_curve.csv'));
I = w.irrigation_mm_yr;
xl = [-90 2090];

fig = new_figure(S.halfW, 7.6);
tl = tiledlayout(fig, 2, 2, 'TileSpacing', 'compact', 'Padding', 'compact');

% (a) long-run cover
ax = nexttile(tl); style_axes(ax, S, 'y');
area_line(ax, I, w.V_steady_pct, c.vegMid, c.veg);
plateau = w.V_steady_pct(end);
plot(ax, xl, [plateau plateau], '--', 'Color', c.limit, 'LineWidth', 0.9);
h1 = plot(ax, I, w.V_steady_pct, 'o', 'MarkerSize', 3.2, 'MarkerFaceColor', 'w', ...
    'MarkerEdgeColor', c.veg, 'LineWidth', 0.8);
h2 = plot(ax, I, w.V_from_planting_pct, 'x', 'MarkerSize', 4, 'Color', c.accent, 'LineWidth', 0.9);
% 300 mm/yr label right of its point (above the legend), 600 mm/yr label upper-left
lab = struct('x0', {300, 600}, 'dx', {90, -60}, 'dy', {-0.3, 1.0}, ...
    'ha', {'left', 'right'}, 'va', {'middle', 'bottom'});
for q = lab
    v = w.V_steady_pct(I == q.x0);
    plot(ax, q.x0, v, 'o', 'MarkerSize', 4.2, 'MarkerFaceColor', c.veg, 'MarkerEdgeColor', 'w', ...
        'LineWidth', 0.5, 'HandleVisibility', 'off');
    text(ax, q.x0 + q.dx, v + q.dy, sprintf('%.1f%%', v), 'FontName', S.font, ...
        'FontSize', S.fs.note, 'Color', c.veg, 'VerticalAlignment', q.va, ...
        'HorizontalAlignment', q.ha);
end
text(ax, 2000, plateau + 0.6, sprintf('%.1f%%', plateau), 'FontName', S.font, ...
    'FontSize', S.fs.note, 'Color', c.limit, 'HorizontalAlignment', 'right', ...
    'VerticalAlignment', 'bottom');
ylim(ax, [0 36]); yticks(ax, 0:10:30);
finish(ax, xl, S, '(a) Long-run cover {\itV}', '%', false);
lg = legend(ax, [h1 h2], {'Long-run state', 'From planting'}, 'Location', 'southeast', ...
    'FontName', S.font, 'FontSize', S.fs.note - 0.5, 'Box', 'off');
lg.ItemTokenSize = [10 6];

% (b) share of demand met
ax = nexttile(tl); style_axes(ax, S, 'y');
plot(ax, xl, [1 1], '--', 'Color', c.limit, 'LineWidth', 0.9);
area_line(ax, I, w.W, c.teal, c.teal);
plot(ax, I, w.W, 'o', 'MarkerSize', 3.2, 'MarkerFaceColor', 'w', 'MarkerEdgeColor', c.teal, ...
    'LineWidth', 0.8);
ylim(ax, [0 1.12]); yticks(ax, 0:0.25:1);
tb = finish(ax, xl, S, '(b) Demand met {\itW}', '', false);
axb = ax;

% (c) year-end store
ax = nexttile(tl); style_axes(ax, S, 'y');
plot(ax, xl, [75 75], '--', 'Color', c.limit, 'LineWidth', 0.9);
text(ax, 0, 76.5, 'capacity {\itC} = 75 mm', 'FontName', S.font, 'FontSize', S.fs.note - 0.5, ...
    'Color', c.limit, 'VerticalAlignment', 'bottom');
area_line(ax, I, w.M_periodic_end_mm, c.waterMid, c.water);
plot(ax, I, w.M_periodic_end_mm, 'o', 'MarkerSize', 3.2, 'MarkerFaceColor', 'w', ...
    'MarkerEdgeColor', c.water, 'LineWidth', 0.8);
ylim(ax, [0 90]); yticks(ax, 0:25:75);
finish(ax, xl, S, '(c) Year-end store {\itM}', 'mm', false);

% (d) sand exposure
ax = nexttile(tl); style_axes(ax, S, 'y');
area_line(ax, I, w.relative_erosion_scenario, c.sand, c.sand);
plot(ax, I, w.relative_erosion_scenario, 'o', 'MarkerSize', 3.2, 'MarkerFaceColor', 'w', ...
    'MarkerEdgeColor', c.sand, 'LineWidth', 0.8);
ylim(ax, [0 1.12]); yticks(ax, 0:0.25:1);
finish(ax, xl, S, '(d) Sand exposure {\itS}', 'relative to bare', false);

xlabel(tl, 'Irrigation on the treated area (mm/yr)', 'FontName', S.font, ...
    'FontSize', S.fs.label, 'Color', c.ink);
% the W-bar is placed in data units, so draw it once the column widths are final
add_overbar(axb, tb);
save_fig(fig, 'm1_water_curve', S);
end

function area_line(ax, x, y, fillc, linec)
% light area under the curve, then the line (阿昆-style filled line plot)
x = x(:); y = y(:);
patch(ax, [x; flipud(x)], [y; zeros(size(y))], fillc, 'FaceAlpha', 0.14, ...
    'EdgeColor', 'none', 'HandleVisibility', 'off');
plot(ax, x, y, '-', 'Color', linec, 'LineWidth', 1.3, 'HandleVisibility', 'off');
end

function t = finish(ax, xl, S, ttl, ylab, overbar)
xlim(ax, xl); xticks(ax, [0 1000 2000]);
ylabel(ax, ylab);
t = panel_title(ax, ttl, S, overbar);
frame_axes(ax, S);
end
