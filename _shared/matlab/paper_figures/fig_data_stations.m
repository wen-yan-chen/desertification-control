function fig_data_stations()
%FIG_DATA_STATIONS Section 3 figure: station network and observed cover.
%   (a) Stations on Esri World Imagery (cached Web Mercator tiles), with the
%       Yutian-Minfeng study transect, a scale bar and a north arrow.
%   (b) Mean growing-season cover V (Jun-Sep, 2015-2025) +- 1 SD across years,
%   Data: Data/v7/m1_audited/{panel_m1.csv, section_definition.json},
%         Data/v7/raw/basemap_tiles/*.jpg
S = paper_style(); c = S.c;
S.fs.title = 8.5;                  % full-width figure
code =["YT" "MF" "QM" "RQ" "KEL" "YL" "ALE" "XT" "TZ"];
lat  = [36.85 37.06 38.13 39.02 41.76 41.34 40.55 38.83 38.97];
lon  = [81.67 82.68 85.53 88.17 86.15 86.26 81.28 84.02 83.65];
cat  = [1 1 1 1 1 1 1 2 3];
catCol = [c.water; c.accent; c.plum];
catLab = ["Category I: oasis margin", "Category II: corridor", "Category III: interior"];
% label offsets in degrees (dx, dy in Mercator-equivalent degrees)
off = [0.25 -0.50; 0.28 -0.12; 0.25 0.20; -0.35 0.33; 0.28 0.15; 0.28 -0.42; ...
       0.28 0.16; 0.28 -0.38; -0.85 0.26];
LON = [79.0 89.6]; LAT = [35.6 42.6];
my = @(la) log(tan(pi / 4 + deg2rad(la) / 2));          % Mercator y (rad)

fig = new_figure(S.textW, 7.7);
tl = tiledlayout(fig, 1, 20, 'TileSpacing', 'compact', 'Padding', 'compact');

% ---------------------------------------------------------------- (a) map
ax = nexttile(tl, 1, [1 11]);
img = basemap(fullfile(S.data, 'raw', 'basemap_tiles'), LON, LAT, 7, my);
img = uint8(0.88 * double(img) + 0.12 * 255);          % light veil: markers read first
image(ax, 'XData', LON, 'YData', [my(LAT(2)) my(LAT(1))], 'CData', img);
style_axes(ax, S, 'none'); ax.Layer = 'top';
set(ax, 'YDir', 'normal', 'DataAspectRatio', [1 pi / 180 1]);
xlim(ax, LON); ylim(ax, my(LAT));
xt = 80:2:88; yt = 36:2:42;
xticks(ax, xt); xticklabels(ax, compose('%d%sE', xt', char(176)));
yticks(ax, my(yt)); yticklabels(ax, compose('%d%sN', yt', char(176)));

% study transect (CON1-CON4), cased so it reads on the imagery
sec = jsondecode(fileread(fullfile(S.data, 'm1_audited', 'section_definition.json')));
cl = sec.centerline;
plot(ax, [cl.lon], my([cl.lat]), '-', 'Color', 'w', 'LineWidth', 3.4);
plot(ax, [cl.lon], my([cl.lat]), '-', 'Color', hex2rgb('F9F871'), 'LineWidth', 1.8);
halo_text(ax, 82.95, my(36.42), sprintf('study section (%.0f km)', sec.polyline_length_km), ...
    hex2rgb('F9F871'), [0.15 0.15 0.15], S, 'FontSize', S.fs.note, 'FontWeight', 'bold');

% stations
for k = 1:numel(code)
    scatter(ax, lon(k), my(lat(k)), 30, catCol(cat(k), :), 'filled', ...
        'MarkerEdgeColor', 'w', 'LineWidth', 0.9);
    halo_text(ax, lon(k) + off(k, 1), my(lat(k)) + deg2rad(off(k, 2)), code(k), ...
        catCol(cat(k), :), [1 1 1], S, 'FontSize', S.fs.label, 'FontWeight', 'bold');
end
halo_text(ax, 84.3, my(39.95), 'Taklamakan Desert', [1 1 1], hex2rgb('5A4630'), S, ...
    'FontSize', S.fs.label + 1, 'FontAngle', 'italic', 'HorizontalAlignment', 'center');

% scale bar (200 km at 36.2 N) and north arrow
km = 111.32 * cosd(36.2);
x0 = 79.35; yb = my(35.95); seg = 100 / km;
for j = 0:1
    patch(ax, x0 + seg * [j j + 1 j + 1 j], yb + [0 0 1 1] * 0.0016, ...
        [1 1 1] * (j == 0) + [0.12 0.12 0.12] * (j == 1), 'EdgeColor', [0.12 0.12 0.12], ...
        'LineWidth', 0.4);
end
for j = 0:2
    halo_text(ax, x0 + seg * j, yb + 0.0019, sprintf('%d', 100 * j), [0.12 0.12 0.12], ...
        [1 1 1], S, 'FontSize', S.fs.note - 1, 'HorizontalAlignment', 'center', ...
        'VerticalAlignment', 'bottom');
end
halo_text(ax, x0 + seg * 2 + 0.12, yb + 0.0008, 'km', [0.12 0.12 0.12], [1 1 1], S, ...
    'FontSize', S.fs.note - 1, 'VerticalAlignment', 'middle');
xn = 89.05; yn = my(41.95);
patch(ax, xn + [-0.17 0 0.17 0], yn + [-0.0062 0.0072 -0.0062 -0.0030], [0.12 0.12 0.12], ...
    'EdgeColor', 'w', 'LineWidth', 0.6);
halo_text(ax, xn, yn + 0.0105, 'N', [0.12 0.12 0.12], [1 1 1], S, ...
    'FontSize', S.fs.label, 'FontWeight', 'bold', 'HorizontalAlignment', 'center');
halo_text(ax, 89.5, my(35.68), 'Basemap: Esri World Imagery', [1 1 1], [0.1 0.1 0.1], S, ...
    'FontSize', S.fs.note - 1.5, 'HorizontalAlignment', 'right', 'VerticalAlignment', 'bottom');

% legend: one entry per category
hs = gobjects(1, 3);
for j = 1:3
    hs(j) = scatter(ax, nan, nan, 30, catCol(j, :), 'filled', 'MarkerEdgeColor', 'w');
end
lg = legend(ax, hs, catLab, 'Location', 'northwest', 'FontName', S.font, ...
    'FontSize', S.fs.note, 'Box', 'on', 'EdgeColor', c.grey, 'Color', [1 1 1]);
lg.ItemTokenSize = [8 6];
panel_title(ax, '(a) Station network', S);
frame_axes(ax, S);

% ------------------------------------------------------------ (b) cover
ax = nexttile(tl, 12, [1 9]); style_axes(ax, S, 'x');
[m, sd, yrs] = cover_stats(fullfile(S.data, 'm1_audited', 'panel_m1.csv'), code);
n = numel(code); y = n:-1:1;
% light band behind each category group
groups = {1:7, 8, 9};
labRow = [8.5 2 1];                % category I label sits in the free space beside YT-MF
for g = 1:3
    yy = y(groups{g});
    patch(ax, [0 50 50 0], [min(yy) - 0.5, min(yy) - 0.5, max(yy) + 0.5, max(yy) + 0.5], ...
        catCol(g, :), 'FaceAlpha', 0.06, 'EdgeColor', 'none');
    text(ax, 49.4, labRow(g), strrep(catLab(g), ': ', newline), 'FontName', S.font, ...
        'FontSize', S.fs.note - 0.5, 'Color', catCol(g, :), 'FontWeight', 'bold', ...
        'HorizontalAlignment', 'right', 'VerticalAlignment', 'middle');
end
plot(ax, [0 50], [2.5 2.5], '-', 'Color', c.grey, 'LineWidth', 0.5);
plot(ax, [0 50], [1.5 1.5], '-', 'Color', c.grey, 'LineWidth', 0.5);
for k = 1:n
    col = catCol(cat(k), :);
    barh(ax, y(k), m(k), 0.6, 'FaceColor', col, 'FaceAlpha', 0.82, 'EdgeColor', 'none');
    errorbar(ax, m(k), y(k), sd(k), 'horizontal', 'Color', c.ink, 'LineWidth', 0.7, ...
        'CapSize', 3, 'LineStyle', 'none');
    text(ax, m(k) + sd(k) + 0.9, y(k), sprintf('%.1f', m(k)), 'FontName', S.font, ...
        'FontSize', S.fs.note, 'Color', c.ink, 'VerticalAlignment', 'middle');
end
xlim(ax, [0 50]); ylim(ax, [0.4 n + 0.6]); xticks(ax, 0:10:50);
yticks(ax, 1:n);
tickCol = catCol(fliplr(cat), :);  % station codes in their category colour
yticklabels(ax, arrayfun(@(k) sprintf('\\color[rgb]{%.3f,%.3f,%.3f}\\bf%s', tickCol(k, :), ...
    code(n + 1 - k)), 1:n, 'UniformOutput', false));
ax.YAxis.TickLength = [0 0];
xlabel(ax, 'Mean growing-season cover {\itV} (%)');
panel_title(ax, ['(b) Observed cover, 2015' char(8211) '2025'], S);
frame_axes(ax, S);
save_fig(fig, 'data_stations', S);
end

% ---------------------------------------------------------------------------
function img = basemap(cache, LON, LAT, z, my)
% Stitch the cached z=7 Web Mercator tiles and crop to the map window.
n = 2 ^ z;
tx = @(lo) (lo + 180) / 360 * n;
ty = @(la) (1 - my(la) / pi) / 2 * n;
fx0 = tx(LON(1)); fx1 = tx(LON(2)); fy0 = ty(LAT(2)); fy1 = ty(LAT(1));
x0 = floor(fx0); x1 = floor(fx1); y0 = floor(fy0); y1 = floor(fy1);
big = zeros((y1 - y0 + 1) * 256, (x1 - x0 + 1) * 256, 3, 'uint8');
for x = x0:x1
    for yy = y0:y1
        t = imread(fullfile(cache, sprintf('%d_%d_%d.jpg', z, x, yy)));
        big((yy - y0) * 256 + (1:256), (x - x0) * 256 + (1:256), :) = t;
    end
end
r = round((fy0 - y0) * 256) + 1 : round((fy1 - y0) * 256);
q = round((fx0 - x0) * 256) + 1 : round((fx1 - x0) * 256);
img = big(r, q, :);
end

function [m, sd, yrs] = cover_stats(file, code)
% Growing-season (Jun-Sep) mean per station-year, then mean and SD across years.
T = readtable(file, 'TextType', 'string');
T.date = datetime(T.date);
T = T(month(T.date) >= 6 & month(T.date) <= 9 & ~isnan(T.V_pct), :);
m = zeros(size(code)); sd = m; yrs = cell(size(code));
for k = 1:numel(code)
    d = T(T.site == code(k), :);
    [g, ~] = findgroups(year(d.date));
    v = splitapply(@mean, d.V_pct, g);
    yrs{k} = v; m(k) = mean(v); sd(k) = std(v);
end
end

function h = halo_text(ax, x, y, str, col, haloCol, S, varargin)
% Text with a thin halo, drawn as offset copies (MATLAB has no path effects).
r = 0.024; ry = deg2rad(r);
for a = 0:pi / 6:2 * pi - 0.1
    text(ax, x + r * cos(a), y + ry * sin(a), str, 'Color', haloCol, 'FontName', S.font, ...
        'Clipping', 'on', varargin{:});
end
h = text(ax, x, y, str, 'Color', col, 'FontName', S.font, 'Clipping', 'on', varargin{:});
end
