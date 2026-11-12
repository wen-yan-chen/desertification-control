function fig_m1_cover_series()
%FIG_M1_COVER_SERIES Paper Fig. "Observed cover at the seven stations" (left half).
%   Observed growing-season cover V, one-step predictions, the free run from
%   2022 and the local ceiling K at each calibration station.
%   Data: Results/v7/model1/{yearly_table, prediction_pairs, free_running_holdout}.csv
S = paper_style(); c = S.c;
S.fs.title = 7.5;               % station names
yt = readtable(fullfile(S.res, 'yearly_table.csv'), 'TextType', 'string');
pp = readtable(fullfile(S.res, 'prediction_pairs.csv'), 'TextType', 'string');
fr = readtable(fullfile(S.res, 'free_running_holdout.csv'), 'TextType', 'string');
sites = ["YT" "MF" "QM" "RQ" "KEL" "YL" "ALE"];
names = ["Yutian" "Minfeng" "Qiemo" "Ruoqiang" "Korla" "Yuli" "Alar"];

fig = new_figure(S.halfW, 12.6);
tl = tiledlayout(fig, 4, 2, 'TileSpacing', 'compact', 'Padding', 'compact');
for i = 1:numel(sites)
    ax = nexttile(tl); style_axes(ax, S, 'y');
    y = sortrows(yt(yt.site == sites(i), :), 'year');
    p = sortrows(pp(pp.site == sites(i), :), 'target_year');
    f = sortrows(fr(fr.site == sites(i), :), 'year');
    K = y.K(1); v22 = f.persistence_2022_pct(1);
    lo = floor(min([y.V; f.predicted_pct]) - 2.5);
    hi = ceil(max([K; y.V]) + 2.5);
    xl = [2014.2 2025.8];

    hb = patch(ax, [2022.5 xl(2) xl(2) 2022.5], [lo lo hi hi], 0.55 * c.sandLight + 0.45, ...
        'EdgeColor', 'none');
    hk = plot(ax, xl, [K K], '--', 'Color', c.limit, 'LineWidth', 1.0);
    hf = plot(ax, [2022; f.year], [v22; f.predicted_pct], '-', 'Color', c.accent, 'LineWidth', 1.8);
    ho = plot(ax, y.year, y.V, '-o', 'Color', c.ink, 'LineWidth', 0.8, 'MarkerSize', 3.2, ...
        'MarkerFaceColor', 'w', 'MarkerEdgeColor', c.ink);
    hd = plot(ax, p.target_year, p.predicted_x .* p.K, 'd', 'MarkerSize', 3.8, ...
        'MarkerFaceColor', c.water, 'MarkerEdgeColor', 'w', 'LineWidth', 0.4);
    text(ax, xl(1) + 0.25, K, '{\itK}', 'Color', c.limit, 'FontName', S.font, ...
        'FontSize', S.fs.note, 'VerticalAlignment', 'bottom');

    xlim(ax, xl); ylim(ax, [lo hi]);
    xticks(ax, [2015 2019 2023]);
    yt_step = 5; if hi - lo > 18, yt_step = 10; end
    yticks(ax, ceil(lo / yt_step) * yt_step : yt_step : hi - 1);   % top tick below the frame
    if i < 6, ax.XTickLabel = []; end     % x labels on the bottom cell of each column
    panel_title(ax, sprintf('%s (%s)', names(i), sites(i)), S);
    frame_axes(ax, S);
end
ylabel(tl, 'Growing-season cover {\itV} (%)', 'FontName', S.font, ...
    'FontSize', S.fs.label, 'Color', c.ink);

lg = legend([ho hd hf hk hb], {'Observed (Jun–Sep)', 'One-step prediction', ...
    'Free run from 2022', 'Local ceiling {\itK}', 'Hold-out 2023–2025'}, 'FontName', S.font, 'FontSize', S.fs.note, ...
    'Box', 'off');
lg.ItemTokenSize = [16 8];
lg.Layout.Tile = 8;
save_fig(fig, 'm1_cover_series', S);
end
