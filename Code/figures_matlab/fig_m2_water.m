function fig_m2_water()
%FIG_M2_WATER Paper Fig. "Annual and monthly water pressure" (right half).
%   (a) annual gross withdrawal vs annual cap, (b) monthly withdrawal by stage
%   vs monthly cap staircase, (c) month-by-year cap utilisation heatmap.
%   Data: Results/v7/model2/{annual.csv, monthly.csv, model2_results.json}
S = paper_style(); c = S.c;
an = readtable(fullfile(S.res2, 'annual.csv'));
mo = readtable(fullfile(S.res2, 'monthly.csv'));
js = jsondecode(fileread(fullfile(S.res2, 'model2_results.json')));
cfg = js.config;

fig = new_figure(S.halfW, 12.2);
tl = tiledlayout(fig, 3, 1, 'TileSpacing', 'compact', 'Padding', 'compact');

% 1. Annual gross withdrawal (10^4 m^3/yr)
ax = nexttile(tl); style_axes(ax, S, 'y');
xl = [0.3 15.7];
acap = cfg.annual_water_cap_m3 / 1e4;
plot(ax, xl, [acap acap], '--', 'Color', c.limit, 'LineWidth', 0.9, 'HandleVisibility', 'off');
text(ax, 0.7, acap + 4, 'annual cap 150 (scenario)', 'FontName', S.font, ...
    'FontSize', S.fs.note - 0.5, 'Color', c.limit, 'VerticalAlignment', 'bottom');
bar(ax, an.year, an.water_m3 / 1e4, 0.62, 'FaceColor', c.waterMid, 'EdgeColor', 'none');
text(ax, 11.5, 117, 'peak 70% of cap', 'FontName', S.font, 'FontSize', S.fs.note, ...
    'Color', c.water, 'FontWeight', 'bold', 'HorizontalAlignment', 'center');
xlim(ax, xl); xticks(ax, 1:2:15);
ylim(ax, [0 176]); yticks(ax, 0:50:150);
xlabel(ax, 'Project year'); ylabel(ax, '10^4 m^3/yr');
panel_title(ax, 'Annual gross water withdrawal {\itQ_t}', S);
frame_axes(ax, S);

% 2. Monthly withdrawal by stage vs monthly cap staircase
ax = nexttile(tl); style_axes(ax, S, 'y');
mcaps = cfg.monthly_water_caps_m3(:)' / 1e4;
hc = stairs(ax, 0.5:1:12.5, [mcaps mcaps(end)], '--', 'Color', c.limit, 'LineWidth', 1.0);
stages = {1, 2, 4, 5, 8};
slabs  = {'Yr 1', 'Yrs 2–3', 'Yr 4', 'Yrs 5–7', 'Yrs 8–15'};
scols  = [hex2rgb('9CC5D6'); hex2rgb('659FB6'); hex2rgb('2B859E'); c.teal; c.water];
hs = gobjects(1, numel(stages));
for k = 1:numel(stages)
    sub = sortrows(mo(mo.year == stages{k}, :), 'month');
    hs(k) = plot(ax, 1:12, sub.gross_water_m3 / 1e4, '-o', 'Color', scols(k, :), ...
        'LineWidth', 1.15, 'MarkerSize', 2.5, 'MarkerFaceColor', 'w', 'MarkerEdgeColor', scols(k, :));
end
% Highlight tightest point: May of years 8-15 (17.1 vs 18.0 -> 95%)
sub8 = sortrows(mo(mo.year == 8, :), 'month');
plot(ax, 5, sub8.gross_water_m3(5) / 1e4, 'o', 'MarkerSize', 4.6, ...
    'MarkerFaceColor', c.limit, 'MarkerEdgeColor', 'w', 'LineWidth', 0.5, 'HandleVisibility', 'off');
text(ax, 4.55, 19.6, 'May: 95%', 'FontName', S.font, 'FontSize', S.fs.note - 0.3, ...
    'Color', c.limit, 'FontWeight', 'bold', 'HorizontalAlignment', 'right');
xlim(ax, [0.4 12.6]); xticks(ax, 1:12);
xticklabels(ax, {'J','F','M','A','M','J','J','A','S','O','N','D'});
ylim(ax, [0 38.5]); yticks(ax, 0:10:30);
ylabel(ax, '10^4 m^3/mo');
lg = legend(ax, [hc hs], [{'Cap {\itQ_m}^{max}'}, slabs], 'Location', 'north', ...
    'FontName', S.font, 'FontSize', S.fs.note - 0.8, 'Box', 'off', 'NumColumns', 3);
lg.ItemTokenSize = [8 5];
panel_title(ax, 'Monthly withdrawal vs. cap', S);
frame_axes(ax, S);

% 3. Month x Year utilisation heatmap (%)
ax = nexttile(tl);
U = zeros(12, 15);
for yr = 1:15
    sub = sortrows(mo(mo.year == yr, :), 'month');
    U(:, yr) = 100 * sub.gross_water_m3 ./ sub.cap_m3;
end
imagesc(ax, 1:15, 1:12, U, [0 100]);
% Smooth sequential palette from very pale ice to deep water teal
anchors = [hex2rgb('F5FAFC'); hex2rgb('CBE3EE'); hex2rgb('659FB6'); hex2rgb('1E5F74'); hex2rgb('113B49')];
cmap = interp1(linspace(0, 1, 5), anchors, linspace(0, 1, 256));
colormap(ax, cmap);
set(ax, 'YDir', 'normal', 'Box', 'off', 'TickDir', 'out', 'TickLength', [0.018 0.018], ...
    'FontName', S.font, 'FontSize', S.fs.tick - 0.5, 'XColor', S.c.axis, 'YColor', S.c.axis, ...
    'LineWidth', 0.6);
hold(ax, 'on');
for yr = 0.5:1:15.5, plot(ax, [yr yr], [0.5 12.5], '-', 'Color', 'w', 'LineWidth', 0.45); end
for m = 0.5:1:12.5,  plot(ax, [0.5 15.5], [m m], '-', 'Color', 'w', 'LineWidth', 0.45); end
% Annotate representative tight cells cleanly without clutter
for yr = [5 8 11 15]
    for m = [4 5 6 7]
        val = U(m, yr);
        if val >= 80
            text(ax, yr, m, sprintf('%.0f', val), 'FontName', S.font, ...
                'FontSize', S.fs.note - 1.1, 'Color', 'w', 'FontWeight', 'bold', ...
                'HorizontalAlignment', 'center', 'VerticalAlignment', 'middle');
        end
    end
end
xlim(ax, [0.5 15.5]); ylim(ax, [0.5 12.5]);
xticks(ax, 1:2:15); yticks(ax, [1 3 5 7 9 11]);
yticklabels(ax, {'Jan','Mar','May','Jul','Sep','Nov'});
xlabel(ax, 'Project year', 'FontName', S.font, 'FontSize', S.fs.label, 'Color', c.ink);
cb = colorbar(ax, 'eastoutside');
cb.FontName = S.font; cb.FontSize = S.fs.note - 0.5; cb.Color = c.axis;
cb.Ticks = 0:25:100; cb.Label.String = '% of cap'; cb.Label.FontSize = S.fs.note;
panel_title(ax, 'Monthly cap use (%) — May reaches 95%', S);
frame_axes(ax, S);

save_fig(fig, 'm2_water', S);
end
