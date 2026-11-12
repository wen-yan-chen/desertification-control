function fig_m1_stress_season()
%FIG_M1_STRESS_SEASON Paper Fig. "The two switches on daily demand".
%   (a) FAO-56 stress coefficient K_s(M) = min{1, M/((1-p)C)}, C = 75 mm,
%       p = 0.5 (tested 0.3-0.7), with the long-run year-end store at 300 and
%       600 mm/yr marked.
%   (b) Season switch f(T) = min{1, max{0, (T-5)/20}} with the section's
%       monthly mean temperature (YT, MF, 2015-2022) on the curve.
%   (c) Monthly reference ET0 and the demand f(T) ET0 used by the model.
%   Data: Data/v7/m1_audited/panel_m1.csv,
%         Results/v7/model1/{section_forcing_climatology, water_cover_curve}.csv
S = paper_style(); c = S.c;
C = 75; p = 0.5; thr = (1 - p) * C;
ks = @(M, pp) min(1, M ./ ((1 - pp) * C));
fT = @(T) min(1, max(0, (T - 5) / 20));

w = readtable(fullfile(S.res, 'water_cover_curve.csv'));
clim = readtable(fullfile(S.res, 'section_forcing_climatology.csv'));
T = section_temperature(fullfile(S.data, 'm1_audited', 'panel_m1.csv'));

fig = new_figure(S.textW, 5.6);
tl = tiledlayout(fig, 1, 3, 'TileSpacing', 'compact', 'Padding', 'compact');

% ------------------------------------------------------------ (a) K_s(M)
ax = nexttile(tl); style_axes(ax, S, 'y');
patch(ax, [0 thr thr 0], [0 0 1.18 1.18], c.sandLight, 'EdgeColor', 'none', 'FaceAlpha', 0.7);
M = linspace(0, C, 301);
for pp = [0.3 0.7]
    plot(ax, M, ks(M, pp), '-', 'Color', c.grey, 'LineWidth', 0.7);
end
patch(ax, [M fliplr(M)], [ks(M, p) zeros(size(M))], c.waterMid, 'FaceAlpha', 0.14, 'EdgeColor', 'none');
plot(ax, M, ks(M, p), '-', 'Color', c.water, 'LineWidth', 1.6);
xline(ax, thr, '--', 'Color', c.limit, 'LineWidth', 0.9);
xline(ax, C, '--', 'Color', c.limit, 'LineWidth', 0.9);
text(ax, thr + 1.5, 0.06, ['(1' char(8722) '{\itp}){\itC}'], 'FontName', S.font, 'FontSize', S.fs.note, ...
    'Color', c.limit, 'VerticalAlignment', 'bottom');
text(ax, C - 1, 0.06, '{\itC}', 'FontName', S.font, 'FontSize', S.fs.note, ...
    'Color', c.limit, 'HorizontalAlignment', 'right', 'VerticalAlignment', 'bottom');
text(ax, thr / 2, 1.09, 'stressed', 'FontName', S.font, 'FontSize', S.fs.note, ...
    'Color', c.sand, 'FontAngle', 'italic', 'HorizontalAlignment', 'center');
text(ax, (thr + C) / 2, 1.09, 'no stress', 'FontName', S.font, 'FontSize', S.fs.note, ...
    'Color', c.water, 'FontAngle', 'italic', 'HorizontalAlignment', 'center');
text(ax, 22.5 * 0.55, 0.63, '{\itp}=0.7', 'FontName', S.font, 'FontSize', S.fs.note - 0.5, ...
    'Color', c.greyDark, 'HorizontalAlignment', 'right');
text(ax, 48, 0.66, '{\itp}=0.3', 'FontName', S.font, 'FontSize', S.fs.note - 0.5, ...
    'Color', c.greyDark, 'HorizontalAlignment', 'left');
% long-run year-end store on the section
for I0 = [300 600]
    m = w.M_periodic_end_mm(w.irrigation_mm_yr == I0);
    plot(ax, m, ks(m, p), 'o', 'MarkerSize', 4.2, 'MarkerFaceColor', c.accent, ...
        'MarkerEdgeColor', 'w', 'LineWidth', 0.6);
    text(ax, m + 1.5, ks(m, p) - 0.03, sprintf('%d mm/yr', I0), 'FontName', S.font, ...
        'FontSize', S.fs.note - 0.5, 'Color', c.accent, 'VerticalAlignment', 'top');
end
xlim(ax, [0 80]); xticks(ax, 0:25:75); ylim(ax, [0 1.18]); yticks(ax, 0:0.25:1);
xlabel(ax, 'Store {\itM} (mm)'); ylabel(ax, '{\itK_s}');
panel_title(ax, '(a) Water stress {\itK_s}({\itM})', S);
frame_axes(ax, S);

% ------------------------------------------------------------ (b) f(T)
ax = nexttile(tl); style_axes(ax, S, 'y');
Tg = linspace(-12, 32, 221);
patch(ax, [Tg fliplr(Tg)], [fT(Tg) zeros(size(Tg))], c.accent, 'FaceAlpha', 0.12, 'EdgeColor', 'none');
plot(ax, Tg, fT(Tg), '-', 'Color', c.accent, 'LineWidth', 1.6);
xline(ax, 5, ':', 'Color', c.greyDark, 'LineWidth', 0.8);
xline(ax, 25, ':', 'Color', c.greyDark, 'LineWidth', 0.8);
text(ax, 5.6, 1.09, '5 °C', 'FontName', S.font, 'FontSize', S.fs.note - 0.5, 'Color', c.greyDark);
text(ax, 24.4, 1.09, '25 °C', 'FontName', S.font, 'FontSize', S.fs.note - 0.5, ...
    'Color', c.greyDark, 'HorizontalAlignment', 'right');
scatter(ax, T, fT(T), 16, c.water, 'filled', 'MarkerEdgeColor', 'w', 'LineWidth', 0.5);
mon = ["Jan" "Feb" "Mar" "Apr" "May" "Jun" "Jul" "Aug" "Sep" "Oct" "Nov" "Dec"];
% month labels: rising months left of the curve, falling months right of it
lab = struct('k', {1, 4, 7, 10}, 'dx', {0, -0.9, 0, 0.9}, 'dy', {0.07, 0.02, -0.07, -0.04}, ...
    'ha', {'center', 'right', 'center', 'left'}, 'va', {'bottom', 'bottom', 'top', 'top'});
for q = lab
    text(ax, T(q.k) + q.dx, fT(T(q.k)) + q.dy, mon(q.k), 'FontName', S.font, ...
        'FontSize', S.fs.note - 0.5, 'Color', c.water, 'HorizontalAlignment', q.ha, ...
        'VerticalAlignment', q.va);
end
xlim(ax, [-12 32]); xticks(ax, -10:10:30); ylim(ax, [0 1.18]); yticks(ax, 0:0.25:1);
xlabel(ax, 'Monthly mean temperature {\itT} (°C)'); ylabel(ax, '{\itf}({\itT})');
panel_title(ax, '(b) Season switch {\itf}({\itT})', S);
frame_axes(ax, S);

% ------------------------------------------------------------ (c) monthly demand
ax = nexttile(tl); style_axes(ax, S, 'y');
b1 = bar(ax, clim.month, clim.ET0_mm, 0.78, 'FaceColor', c.grid, 'EdgeColor', c.grey, 'LineWidth', 0.4);
b2 = bar(ax, clim.month, clim.ET0g_mm, 0.50, 'FaceColor', c.water, 'EdgeColor', 'none');
xlim(ax, [0.3 12.7]); xticks(ax, [1 4 7 10]); xticklabels(ax, mon([1 4 7 10]));
ylim(ax, [0 330]); yticks(ax, 0:50:250);
xlabel(ax, 'Month'); ylabel(ax, 'mm per month');
lg = legend(ax, [b1 b2], {sprintf('{\\itET}_0  (%s mm/yr)', thousands(sum(clim.ET0_mm))), ...
    sprintf('{\\itf}({\\itT}) {\\itET}_0  (%s mm/yr)', thousands(sum(clim.ET0g_mm)))}, ...
    'Location', 'north', 'FontName', S.font, 'FontSize', S.fs.note - 0.5, 'Box', 'off');
lg.ItemTokenSize = [9 6];
panel_title(ax, '(c) Monthly demand', S);
frame_axes(ax, S);
save_fig(fig, 'm1_stress_season', S);
end

% ---------------------------------------------------------------------------
function T = section_temperature(file)
% Monthly mean air temperature on the section (YT, MF), training years 2015-2022.
P = readtable(file, 'TextType', 'string');
P.date = datetime(P.date);
P = P(ismember(P.site, ["YT" "MF"]) & year(P.date) <= 2022, :);
T = splitapply(@mean, P.era_T, month(P.date));
end

function s = thousands(x)
s = regexprep(sprintf('%.0f', x), '(\d)(?=(\d{3})+$)', '$1,');
end
