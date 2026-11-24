function fig_m1_sensitivity()
%FIG_M1_SENSITIVITY Paper Fig. "Sensitivity of long-run cover".
%   (a)(b) one-at-a-time tornado at 300 and 600 mm/yr; (c) wind speed scaled
%   inside ET0 at 300 mm/yr.
%   Data: Results/v7/model1/{sensitivity, water_cover_curve}.csv, model1_results.json
S = paper_style(); c = S.c;
s = readtable(fullfile(S.res, 'sensitivity.csv'), 'TextType', 'string');
w = readtable(fullfile(S.res, 'water_cover_curve.csv'));
base = @(I) w.V_steady_pct(w.irrigation_mm_yr == I);

par  = ["capacity_mm" "rain_fraction" "c" "eta_w" "depletion_fraction" "v_full_pct"];
labs = ["Storage capacity {\itC}", "Rain to roots \alpha_{\itP}", ...
        "Transpiration coeff. {\itc}", "Irrigation to roots \eta_{\itw}", ...
        "Stress-free share {\itp}", "End-member {\itV}_{full}"];
% one row order for both panels, ranked by the 300 mm/yr swing (largest on top)
swing = zeros(size(par));
for k = 1:numel(par)
    d = s(s.parameter == par(k) & s.irrigation_mm_yr == 300, :);
    swing(k) = max(abs(d.V_pct - base(300)));
end
[~, order] = sort(swing, 'ascend');

fig = new_figure(S.halfW, 11.6);
tl = tiledlayout(fig, 14, 1, 'TileSpacing', 'compact', 'Padding', 'compact');
spans = {[1 5], [6 5]};
Is = [300 600];
for p = 1:2
    ax = nexttile(tl, spans{p}(1), [spans{p}(2) 1]); style_axes(ax, S, 'x');
    I = Is(p); b0 = base(I);
    for r = 1:numel(order)
        k = order(r);
        d = sortrows(s(s.parameter == par(k) & s.irrigation_mm_yr == I, :), 'value');
        dlo = d.V_pct(1) - b0; dhi = d.V_pct(end) - b0;
        if mod(r, 2) == 0   % zebra rows help the eye across the labels
            patch(ax, [-4.4 4.4 4.4 -4.4], r + [-0.5 -0.5 0.5 0.5], c.grid, ...
                'EdgeColor', 'none', 'FaceAlpha', 0.6, 'HandleVisibility', 'off');
        end
        hl = barh(ax, r, dlo, 0.62, 'FaceColor', c.water, 'EdgeColor', 'none');
        hh = barh(ax, r, dhi, 0.62, 'FaceColor', c.accent, 'EdgeColor', 'none');
        vals = [d.value(1) d.value(end)]; dv = [dlo dhi];
        [~, left] = min(dv); right = 3 - left;
        text(ax, min([dv 0]) - 0.12, r, num2str(vals(left), '%g'), 'FontName', S.font, ...
            'FontSize', S.fs.note - 0.5, 'Color', c.greyDark, 'HorizontalAlignment', 'right');
        text(ax, max([dv 0]) + 0.12, r, num2str(vals(right), '%g'), 'FontName', S.font, ...
            'FontSize', S.fs.note - 0.5, 'Color', c.greyDark, 'HorizontalAlignment', 'left');
    end
    xline(ax, 0, '-', 'Color', c.ink, 'LineWidth', 0.8, 'HandleVisibility', 'off');
    xlim(ax, [-4.4 4.4]); ylim(ax, [0.4 numel(order) + 0.6]);
    yticks(ax, 1:numel(order)); yticklabels(ax, labs(order));
    ax.YAxis.TickLength = [0 0];
    ax.YAxis.FontSize = S.fs.note;
    if p == 1
        ax.XTickLabel = [];
    else
        xlabel(ax, 'Change in long-run cover {\itV} (percentage points)');
    end
    panel_title(ax, sprintf('(%c) %d mm/yr, baseline %.1f%%', 'a' + p - 1, I, b0), S);
    frame_axes(ax, S);
end
lg = legend(ax, [hl hh], {'Low tested value', 'High tested value'}, 'FontName', S.font, ...
    'FontSize', S.fs.note, 'Box', 'off', 'Orientation', 'horizontal');
lg.ItemTokenSize = [12 7];
lg.Layout.Tile = 'north';

% (c) wind speed scaled inside ET0
ax = nexttile(tl, 11, [4 1]); style_axes(ax, S, 'y');
k = sortrows(s(s.parameter == "wind_speed_scale" & s.irrigation_mm_yr == 300, :), 'value');
x = 100 * (k.value - 1);
patch(ax, [x; flipud(x)], [k.V_pct; 16.6 * ones(size(x))], c.sand, 'FaceAlpha', 0.12, ...
    'EdgeColor', 'none');
plot(ax, x, k.V_pct, '-', 'Color', c.sand, 'LineWidth', 1.3);
plot(ax, x, k.V_pct, 'o', 'MarkerSize', 3.8, 'MarkerFaceColor', 'w', 'MarkerEdgeColor', c.sand, ...
    'LineWidth', 0.9);
for j = 1:height(k)
    text(ax, x(j), k.V_pct(j) + 0.14, sprintf('%.1f', k.V_pct(j)), 'FontName', S.font, ...
        'FontSize', S.fs.note, 'Color', c.sand, 'VerticalAlignment', 'bottom', ...
        'HorizontalAlignment', 'center');
end
xlim(ax, [-25 25]); xticks(ax, -20:10:20); ylim(ax, [16.6 19.4]); yticks(ax, 17:19);
xlabel(ax, 'Change in wind speed (%)');
ylabel(ax, '{\itV} (%)');
panel_title(ax, '(c) Wind speed, 300 mm/yr', S);
frame_axes(ax, S);
save_fig(fig, 'm1_sensitivity', S);
end
