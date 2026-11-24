function fig_m1_scenarios()
%FIG_M1_SCENARIOS Paper Fig. "Scenario paths on the section, 2026-2050" (right half).
%   Cover V, year-end store M and demand met W-bar for constant irrigation
%   quotas, plus 600 mm/yr stopped after 2035.
%   Data: Results/v7/model1/scenario_annual.csv
S = paper_style(); c = S.c;
a = readtable(fullfile(S.res, 'scenario_annual.csv'), 'TextType', 'string');
scen = ["I0" "I100" "I300" "I600" "I1000" "I2000"];
labs = ["0" "100" "300" "600" "1000" "2000"];
cols = {'V_end_pct', 'M_end_mm', 'W'};
titles = {'Cover proxy {\itV}', 'Store {\itM} at year end', 'Share of demand met {\itW}'};
units = {'%', 'mm', ''};
xl = [2025.3 2053.6];

fig = new_figure(S.halfW, 12.6);
tl = tiledlayout(fig, 3, 1, 'TileSpacing', 'compact', 'Padding', 'compact');
h = gobjects(1, numel(scen) + 1);
for k = 1:3
    ax = nexttile(tl); style_axes(ax, S, 'y');
    for j = 1:numel(scen)
        d = a(a.scenario == scen(j), :);
        h(j) = plot(ax, d.calendar_year, d.(cols{k}), '-', 'Color', c.ramp(j, :), 'LineWidth', 1.3);
    end
    % identical to 600 mm/yr through 2035, so drawn from where it departs
    d = a(a.scenario == "stop_after_10" & a.calendar_year >= 2035, :);
    h(end) = plot(ax, d.calendar_year, d.(cols{k}), '-', 'Color', c.accent, 'LineWidth', 1.9);
    xline(ax, 2035.5, ':', 'Color', c.greyDark, 'LineWidth', 0.9, 'HandleVisibility', 'off');
    xlim(ax, xl); xticks(ax, [2026 2034 2042 2050]);
    ylabel(ax, units{k});
    if k < 3, ax.XTickLabel = []; end
    if k == 1
        ylim(ax, [0 34]); yticks(ax, 0:10:30);
        text(ax, 2035.9, 32.2, 'irrigation stops', 'FontName', S.font, 'FontSize', S.fs.note, ...
            'Color', c.greyDark, 'FontAngle', 'italic', 'VerticalAlignment', 'middle');
        % end-of-run values in the colour of their line
        end_lab(ax, a, scen(2:end), c.ramp(2:end, :), S);
        end_lab(ax, a, "stop_after_10", c.accent, S);
    elseif k == 2
        ylim(ax, [0 82]); yticks(ax, 0:20:80);
    else
        ylim(ax, [0 1.08]); yticks(ax, 0:0.25:1);
    end
    panel_title(ax, titles{k}, S, k == 3);
    frame_axes(ax, S);
end
lg = legend(h, [labs + " mm/yr", "600, stop after 2035"], 'FontName', S.font, ...
    'FontSize', S.fs.note, 'Box', 'off', 'NumColumns', 3);
lg.ItemTokenSize = [14 8];
lg.Layout.Tile = 'south';
save_fig(fig, 'm1_scenarios', S);
end

function end_lab(ax, a, scen, cols, S)
for j = 1:numel(scen)
    v = a.V_end_pct(a.scenario == scen(j) & a.calendar_year == 2050);
    text(ax, 2050.7, v, sprintf('%.0f', v), 'Color', cols(j, :), 'FontName', S.font, ...
        'FontSize', S.fs.note, 'FontWeight', 'bold', 'VerticalAlignment', 'middle');
end
end
