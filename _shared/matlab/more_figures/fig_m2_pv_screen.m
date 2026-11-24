function fig_m2_pv_screen()
%FIG_M2_PV_SCREEN Paper Fig. "Standalone PV break-even tariff and 15-yr NPV".
%   (a) Break-even price p_e^{BE}(s) vs build year s (log y-scale),
%   (b) Standalone 15-yr NPV per kW, annotated with MW built in the base plan.
%   Data: Results/v7/model2/{pv_screening.csv, decisions.csv, model2_results.json}
S = paper_style(); c = S.c;
pv = readtable(fullfile(S.res2, 'pv_screening.csv'));
dc = readtable(fullfile(S.res2, 'decisions.csv'), 'TextType', 'string');
dc_pv = dc(dc.kind == "pv", :);
s = pv.start_year;
built = ismember(s, dc_pv.start_year);
xl = [0.3 14.7];

fig = new_figure(S.halfW, 7.8);
tl = tiledlayout(fig, 2, 1, 'TileSpacing', 'compact', 'Padding', 'compact');

% (a) Break-even tariff (CNY/kWh, log scale)
ax = nexttile(tl); style_axes(ax, S, 'y');
set(ax, 'YScale', 'log', 'YMinorTick', 'off', 'YMinorGrid', 'off');
plot(ax, xl, [0.40 0.40], ':', 'Color', c.greyDark, 'LineWidth', 0.8, 'HandleVisibility', 'off');
plot(ax, xl, [0.15 0.15], ':', 'Color', c.greyDark, 'LineWidth', 0.8, 'HandleVisibility', 'off');
plot(ax, xl, [0.30 0.30], '--', 'Color', c.limit, 'LineWidth', 0.95, 'HandleVisibility', 'off');
text(ax, 14.4, 0.285, 'base tariff 0.30 CNY/kWh', 'FontName', S.font, ...
    'FontSize', S.fs.note - 0.4, 'Color', c.limit, 'HorizontalAlignment', 'right', 'VerticalAlignment', 'top');
text(ax, 14.4, 0.415, 'high 0.40', 'FontName', S.font, 'FontSize', S.fs.note - 0.6, ...
    'Color', c.greyDark, 'HorizontalAlignment', 'right', 'VerticalAlignment', 'bottom');
text(ax, 14.4, 0.156, 'low 0.15', 'FontName', S.font, 'FontSize', S.fs.note - 0.6, ...
    'Color', c.greyDark, 'HorizontalAlignment', 'right', 'VerticalAlignment', 'bottom');

plot(ax, s, pv.break_even_price_cny_kwh, '-', 'Color', c.pvDark, 'LineWidth', 1.25, 'HandleVisibility', 'off');
h1 = plot(ax, s(built), pv.break_even_price_cny_kwh(built), 'o', 'MarkerSize', 4.4, ...
    'MarkerFaceColor', c.accent, 'MarkerEdgeColor', c.pvDark, 'LineWidth', 0.8);
h2 = plot(ax, s(~built), pv.break_even_price_cny_kwh(~built), 'o', 'MarkerSize', 4.2, ...
    'MarkerFaceColor', 'w', 'MarkerEdgeColor', c.pvDark, 'LineWidth', 0.9);
xlim(ax, xl); xticks(ax, 1:2:13); ax.XTickLabel = [];
ylim(ax, [0.125 2.8]); yticks(ax, [0.15 0.30 0.60 1.20 2.40]);
yticklabels(ax, {'0.15','0.30','0.60','1.20','2.40'});
ylabel(ax, 'CNY/kWh (log)');
lg = legend(ax, [h1 h2], {'Built in base (yrs 1–4)', 'Screened out (yrs \geq 5)'}, ...
    'Location', 'northwest', 'FontName', S.font, 'FontSize', S.fs.note - 0.5, 'Box', 'off');
lg.ItemTokenSize = [10 6];
panel_title(ax, '(a) Break-even tariff {\itp_e}^{BE}({\its})', S);
frame_axes(ax, S);

% (b) Standalone 15-yr NPV (CNY/kW)
ax = nexttile(tl); style_axes(ax, S, 'y');
yline(ax, 0, '-', 'Color', c.ink, 'LineWidth', 0.75);
npv = pv.standalone_npv_cny_per_kw;
bar(ax, s(built), npv(built), 0.62, 'FaceColor', c.accent, 'EdgeColor', 'none');
bar(ax, s(~built), npv(~built), 0.62, 'FaceColor', 'w', 'EdgeColor', c.pvDark, 'LineWidth', 0.85);
for k = 1:height(dc_pv)
    yr = dc_pv.start_year(k);
    mw = dc_pv.capacity_kw(k) / 1e3;
    v  = npv(s == yr);
    text(ax, yr, v + 85, sprintf('%.1f', mw), 'FontName', S.font, ...
        'FontSize', S.fs.note - 0.6, 'Color', c.pvDark, 'FontWeight', 'bold', ...
        'HorizontalAlignment', 'center', 'VerticalAlignment', 'bottom');
end
text(ax, 14.3, 860, 'numbers: MW built in base', 'FontName', S.font, ...
    'FontSize', S.fs.note - 0.6, 'Color', c.greyDark, 'HorizontalAlignment', 'right');
xlim(ax, xl); xticks(ax, 1:2:13);
ylim(ax, [-2900 1150]); yticks(ax, -2000:1000:1000);
xlabel(ax, 'Construction year {\its}'); ylabel(ax, 'CNY/kW');
panel_title(ax, '(b) Standalone 15-year NPV', S);
frame_axes(ax, S);

save_fig(fig, 'm2_pv_screen', S);
end
