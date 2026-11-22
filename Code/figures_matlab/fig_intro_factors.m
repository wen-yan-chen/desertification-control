function fig_intro_factors()
%FIG_INTRO_FACTORS Introduction figure: the four management factors.
%   Centre: shelterbelt on dunes along the Tarim Desert Highway. Side tiles:
%   water supply, labour, funding and disaster shocks, each with a title bar.
%   Replaces the former factor table at about the same height.
%   Photos and licences: Data/v7/raw/photos/README.md.
S = paper_style(); c = S.c;
W = S.textW; H = 5.5;
g  = 0.12;                         % gap between panels (cm)
ws = 4.35;                         % side tile width (cm)
wh = W - 2 * ws - 2 * g;           % centre width (cm)
ht = (H - g) / 2;                  % side tile height (cm)
P  = fullfile(S.data, 'raw', 'photos');

fig = new_figure(W, H);
cm = @(x, y, w, h) [x / W, y / H, w / W, h / H];

% name, photo, colour, glyph, crop window [x0 x1 y0 y1] (px), contrast gain, position (cm)
T = struct( ...
    'name',  {'Water supply', 'Labour', 'Funding', 'Disaster shocks'}, ...
    'file',  {'tarim_river_canopus.jpg', 'straw_checkerboard_qiemo_maki.jpg', ...
              'pv_wind_xinjiang_w0zny.jpg', 'dust_storm_modis_20180408.jpg'}, ...
    'col',   {c.water, c.veg, c.plum, c.limit}, ...
    'glyph', {'drop', 'person', 'coin', 'wind'}, ...
    'win',   {[40 1100 400 1060], [176 3580 160 2460], [150 1130 20 672], [60 1200 110 870]}, ...
    'gain',  {1.18, 1, 1, 1}, ...
    'pos',   {cm(0, ht + g, ws, ht), cm(0, 0, ws, ht), ...
              cm(W - ws, ht + g, ws, ht), cm(W - ws, 0, ws, ht)});

% centre photo
ax = axes(fig, 'Position', cm(ws + g, 0, wh, H));
img = crop_to(imread(fullfile(P, 'shelterbelt_dunes_canopus.jpg')), [120 3216 235 2136], wh / H, 'left');
show(ax, img);
[nyH, nxH, ~] = size(img);
tag(ax, 0.035 * nxH, 0.075 * nyH, 'Protective belt', c.veg, nyH / H, S);

for k = 1:numel(T)
    t = T(k);
    ax = axes(fig, 'Position', t.pos);
    img = crop_to(imread(fullfile(P, t.file)), t.win, ws / ht, 'centre');
    img = uint8(min(255, max(0, 127.5 + t.gain * (double(img) - 127.5))));   % lift flat overcast photo
    show(ax, img);
    title_bar(ax, img, t.name, t.col, t.glyph, size(img, 1) / ht, S);
end

save_fig(fig, 'intro_factors', S);
end

function img = crop_to(img, win, aspect, align)
% Largest window of the given width/height ratio inside win = [x0 x1 y0 y1].
w = win(2) - win(1); h = win(4) - win(3);
if w / h > aspect
    nw = round(h * aspect); nh = h;
    if strcmp(align, 'left'), x0 = win(1); else, x0 = win(1) + round((w - nw) / 2); end
    y0 = win(3);
else
    nw = w; nh = round(w / aspect);
    x0 = win(1); y0 = win(3) + round((h - nh) / 2);
end
img = img(y0 + 1:y0 + nh, x0 + 1:x0 + nw, :);
end

function show(ax, img)
image(ax, img); hold(ax, 'on');
set(ax, 'XLim', [0.5 size(img, 2) + 0.5], 'YLim', [0.5 size(img, 1) + 0.5], ...
    'Visible', 'off', 'XTick', [], 'YTick', []);
end

function title_bar(ax, img, name, col, glyph, pxPerCm, S)
% Opaque colour bar along the top edge with a white badge and white title.
nx = size(img, 2);
hb = 0.56 * pxPerCm;
patch(ax, [0.5 nx + 0.5 nx + 0.5 0.5], [0.5 0.5 hb hb], col, 'EdgeColor', 'none');
R  = 0.19 * pxPerCm;
bx = 0.16 * pxPerCm + R; by = hb / 2;
draw_badge(ax, bx, by, R, [1 1 1], col, glyph, S);
text(ax, bx + R + 0.12 * pxPerCm, by + 0.01 * pxPerCm, name, 'FontName', S.font, ...
    'FontSize', 9.5, 'FontWeight', 'bold', 'Color', [1 1 1], 'VerticalAlignment', 'middle');
end

function tag(ax, x, y, str, col, pxPerCm, S)
% White rounded label with a coloured outline, top-left anchored.
t = text(ax, 0, 0, str, 'FontName', S.font, 'FontSize', 9.5, 'FontWeight', 'bold', ...
    'Color', col, 'VerticalAlignment', 'middle');
e = t.Extent; pad = 0.14 * pxPerCm; hBox = 0.56 * pxPerCm;
[xr, yr] = round_rect(x, y, e(3) + 2 * pad, hBox, 0.12 * pxPerCm);
patch(ax, xr, yr, [1 1 1], 'EdgeColor', col, 'LineWidth', 0.8);
t.Position = [x + pad, y + hBox / 2, 0];
uistack(t, 'top');
end

function [x, y] = round_rect(x0, y0, w, h, r)
th = linspace(0, pi / 2, 12);
cx = [x0 + w - r, x0 + r, x0 + r, x0 + w - r];
cy = [y0 + h - r, y0 + h - r, y0 + r, y0 + r];
x = []; y = [];
for i = 1:4
    a = (i - 1) * pi / 2 + th;
    x = [x, cx(i) + r * cos(a)]; %#ok<AGROW>
    y = [y, cy(i) + r * sin(a)]; %#ok<AGROW>
end
end

function draw_badge(ax, cx, cy, R, bg, fg, glyph, S)
th = linspace(0, 2 * pi, 60);
patch(ax, cx + R * cos(th), cy + R * sin(th), bg, 'EdgeColor', 'none');
switch glyph
    case 'drop'      % cusp up (image y grows downward)
        t = linspace(0, 2 * pi, 80);
        patch(ax, cx + 0.50 * R * sin(t) .* sin(t / 2) .^ 1.3, ...
                  cy + 0.10 * R - 0.62 * R * cos(t), fg, 'EdgeColor', 'none');
    case 'coin'
        text(ax, cx, cy, char(165), 'FontName', S.font, 'FontSize', 8, ...
            'FontWeight', 'bold', 'Color', fg, 'HorizontalAlignment', 'center', ...
            'VerticalAlignment', 'middle');
    case 'person'
        patch(ax, cx + 0.24 * R * cos(th), cy - 0.30 * R + 0.24 * R * sin(th), fg, 'EdgeColor', 'none');
        a = linspace(pi, 2 * pi, 30);
        patch(ax, [cx + 0.50 * R * cos(a), cx + 0.50 * R], ...
                  [cy + 0.55 * R + 0.50 * R * sin(a), cy + 0.55 * R], fg, 'EdgeColor', 'none');
    case 'wind'
        lw = 0.9;
        a = linspace(-pi / 2, pi, 24); r = 0.17 * R;
        xa = cx + 0.22 * R; ya = cy - 0.32 * R - r;
        plot(ax, [cx - 0.58 * R, xa, xa + r * cos(a)], ...
                 [cy - 0.32 * R, cy - 0.32 * R, ya - r * sin(a)], '-', 'Color', fg, 'LineWidth', lw);
        plot(ax, [cx - 0.62 * R, cx + 0.56 * R], [cy + 0.02 * R, cy + 0.02 * R], '-', 'Color', fg, 'LineWidth', lw);
        xb = cx + 0.10 * R; yb = cy + 0.36 * R + r;
        plot(ax, [cx - 0.48 * R, xb, xb + r * cos(-a)], ...
                 [cy + 0.36 * R, cy + 0.36 * R, yb + r * sin(-a)], '-', 'Color', fg, 'LineWidth', lw);
end
end
