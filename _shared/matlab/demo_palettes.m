function demo_palettes(out)
%DEMO_PALETTES Palette sheet, colour-map sheet and one sample figure per palette.
%   Run from this folder:  matlab -batch demo_palettes
%   Writes palettes.png and colormaps.png to ../gallery and
%   <name>.png for every palette to ../gallery/palettes (or under the folder given).
here = fileparts(mfilename('fullpath'));
addpath(here, fullfile(here, 'charts'));
if nargin < 1, out = fullfile(here, '..', 'gallery'); end
S = paper_style('out', out); S.pdf = false; S.dpi = 220; c = S.c;
names = kit_palette(); n = numel(names);
txt = @(ax, x, y, s, varargin) text(ax, x, y, s, 'FontName', S.font, 'Interpreter', 'none', varargin{:});

% ---------------------------------------------------------- palette sheet
W = 18.5; rh = 2.35; top = 0.85; H = top + n * rh + 0.15;
[fig, ax] = canvas(W, H);
roles = {'1 Main', '2 Accent', '3 Green/Mid', '4 Secondary', '5 Warm/Earth', '6 Extra'};
xSw = 4.35; sw = 1.22; gap = 0.10;
for j = 1:6
    txt(ax, xSw + (j - 1) * (sw + gap) + sw / 2, 0.52, roles{j}, 'FontSize', 6.3, ...
        'Color', c.greyDark, 'HorizontalAlignment', 'center');
end
txt(ax, 13.58, 0.52, 'Lines + band', 'FontSize', 6.3, 'Color', c.greyDark, 'HorizontalAlignment', 'center');
txt(ax, 16.70, 0.52, 'Stacked + bars', 'FontSize', 6.3, 'Color', c.greyDark, 'HorizontalAlignment', 'center');
t = linspace(0, 1, 40);
for i = 1:n
    P = kit_palette(names{i}); cols = P.cycle; y = top + (i - 1) * rh;
    plot(ax, [0.30 W - 0.30], [y y], '-', 'Color', c.grid, 'LineWidth', 0.6);
    txt(ax, 0.35, y + 0.48, P.title, 'FontSize', 9.2, 'FontWeight', 'bold', 'Color', c.ink);
    txt(ax, 0.35, y + 0.92, ['''' P.name ''''], 'FontName', 'Courier New', 'FontSize', 6.8, 'Color', c.axis);
    txt(ax, 0.35, y + 1.30, P.source, 'FontSize', 6.1, 'Color', c.greyDark);
    if P.safe
        patch(ax, 0.35 + [0 2.05 2.05 0], y + 1.54 + [0 0 0.38 0.38], [0.91 0.96 0.93], ...
            'EdgeColor', [0.35 0.62 0.48], 'LineWidth', 0.45);
        txt(ax, 0.35 + 1.025, y + 1.73, 'colorblind-safe', 'FontSize', 5.8, ...
            'Color', [0.16 0.42 0.28], 'HorizontalAlignment', 'center', 'VerticalAlignment', 'middle');
    end
    for j = 1:6
        xs = xSw + (j - 1) * (sw + gap);
        patch(ax, xs + [0 sw sw 0], y + 0.32 + [0 0 1.28 1.28], cols(j, :), 'EdgeColor', 'none');
        txt(ax, xs + sw / 2, y + 1.85, ['#' P.hex{j}], 'FontName', 'Courier New', ...
            'FontSize', 5.8, 'Color', c.axis, 'HorizontalAlignment', 'center');
    end
    xl = 12.35; wl = 2.45; yb = y + 1.69; ht = 1.32;
    patch(ax, xl + [0 wl wl 0], yb - [0 0 ht ht], [0.985 0.988 0.99], 'EdgeColor', c.grid, 'LineWidth', 0.45);
    y1 = 0.25 + 0.62 * exp(-2.2 * t); y2 = 0.16 + 0.45 * exp(-1.7 * t); y3 = 0.08 + 0.28 * exp(-2.8 * t);
    b1 = 0.09 * (1 + 0.4 * t);
    patch(ax, xl + wl * [t fliplr(t)], yb - ht * [min(0.96, y1 + b1), fliplr(max(0.04, y1 - b1))], ...
        cols(1, :), 'FaceAlpha', 0.16, 'EdgeColor', 'none');
    plot(ax, xl + wl * t, yb - ht * y1, '-', 'Color', cols(1, :), 'LineWidth', 1.35);
    plot(ax, xl + wl * t, yb - ht * y2, '-', 'Color', cols(3, :), 'LineWidth', 1.25);
    plot(ax, xl + wl * t, yb - ht * y3, '-', 'Color', cols(2, :), 'LineWidth', 1.25);
    xb = 15.20; wb = 3.00;
    patch(ax, xb + [0 wb wb 0], yb - [0 0 ht ht], [0.985 0.988 0.99], 'EdgeColor', c.grid, 'LineWidth', 0.45);
    s1 = [0.28 0.34 0.38]; s2 = [0.42 0.26 0.32]; sx = xb + 0.12; swb = 1.30;
    for rowb = 1:2
        if rowb == 1, sh = s1; idxC = [1 4 2]; yy = yb - 0.92; else, sh = s2; idxC = [3 5 6]; yy = yb - 0.42; end
        cur = 0;
        for q = 1:3
            patch(ax, sx + swb * [cur cur + sh(q) cur + sh(q) cur], yy + [0 0 0.30 0.30], ...
                cols(idxC(q), :), 'EdgeColor', 'w', 'LineWidth', 0.4);
            cur = cur + sh(q);
        end
    end
    gx = xb + 1.62; bh = [0.78 0.96 0.62 0.84];
    for q = 1:4
        bx = gx + (q - 1) * 0.31;
        patch(ax, bx + [0 0.23 0.23 0], yb - 0.08 - [0 0 bh(q) * 1.12 bh(q) * 1.12], cols(q, :), 'EdgeColor', 'none');
    end
end
save_fig(fig, 'palettes', S);
W = S.textW;

% -------------------------------------------------------- colour-map sheet
M = {'seq',     'one-sided quantity (follows the palette)'; ...
     'green',   'cover or benefit (follows the palette)'; ...
     'warm',    'pressure or risk (follows the palette)'; ...
     'div',     'deviation from a centre (follows the palette)'; ...
     'ramp',    'short to long, as in bars3d (follows the palette)'; ...
     'viridis', 'sequential, reads in greyscale, colour-blind safe (matplotlib)'; ...
     'cividis', 'sequential, colour-blind safe (Nunez et al. 2018)'; ...
     'ylgnbu',  'sequential, light background (ColorBrewer)'; ...
     'rdbu',    'diverging, red-blue (ColorBrewer)'};
m = size(M, 1); rh = 1.0; H = 0.25 + m * rh;
[fig, ax] = canvas(W, H);
for i = 1:m
    y = 0.25 + (i - 1) * rh; cm = kit_cmap(S, M{i, 1}, 200);
    txt(ax, 0.25, y + 0.33, ['''' M{i, 1} ''''], 'FontName', 'Courier New', 'FontSize', 8, 'FontWeight', 'bold', 'Color', c.ink);
    image(ax, 'XData', [2.4 9.4] + [0.5 -0.5] * 7 / 200, 'YData', y + [0.21 0.51], 'CData', repmat(reshape(cm, 1, [], 3), 2, 1));
    txt(ax, 9.75, y + 0.33, M{i, 2}, 'FontSize', 6.8, 'Color', c.axis);
end
save_fig(fig, 'colormaps', S);

% ------------------------------------------------ one sample figure per palette
t = (0:50)'; Y = [9 + 14 * exp(-t / 16), 7 + 10 * exp(-t / 11), 2 + 13 * exp(-t / 7)];
R = [1 .62 -.41 .18 -.55; .62 1 -.22 .35 -.30; -.41 -.22 1 -.08 .71; .18 .35 -.08 1 .12; -.55 -.30 .71 .12 1];
for i = 1:n
    S = paper_style('out', fullfile(out, 'palettes'), 'palette', names{i}); S.pdf = false; S.dpi = 220; c = S.c;
    fig = new_figure(S.textW, 5.6);
    tl = tiledlayout(fig, 1, 3, 'TileSpacing', 'loose', 'Padding', 'compact');
    for k = 1:3, nexttile(tl, k); end
    ax = nexttile(tl, 1);
    band_lines(ax, t, Y, S, 'lo', Y - [2.5 2 1.2] .* (1 + t / 60), 'hi', Y + [2.5 2 1.2] .* (1 + t / 60), ...
        'names', {'High', 'Mid', 'Low'}, 'colors', [c.water; c.veg; c.sand]);
    xticks(ax, 0:10:50); xlabel(ax, 'Year'); ylabel(ax, 'Cover (%)'); frame_axes(ax, S);
    ax = nexttile(tl, 2);
    stacked_bars(ax, [22 34 44; 40 60 0; 30 45 25; 18 52 30], {'Base', 'No PV', 'Low tariff', 'High upkeep'}, S, ...
        'names', {'Build', 'O&M', 'PV'}, 'colors', [c.vegMid; c.plum; c.accent]);
    xlabel(ax, 'Share of spending (%)'); frame_axes(ax, S);
    ax = nexttile(tl, 3);
    heatmap_grid(ax, R, S, 'xlabels', {'V', 'M', 'E', 'T', 'S'}, 'ylabels', {'V', 'M', 'E', 'T', 'S'}, ...
        'clim', [-1 1], 'cmap', 'div', 'fmt', '%.2f', 'cbar', 'Correlation');
    frame_axes(ax, S);
    save_fig(fig, names{i}, S);
end
end

function [fig, ax] = canvas(W, H)
% Blank page in centimetres, y pointing down.
fig = new_figure(W, H);
ax = axes(fig, 'Position', [0 0 1 1]); hold(ax, 'on'); axis(ax, 'off');
set(ax, 'YDir', 'reverse', 'XLim', [0 W], 'YLim', [0 H]);
end
