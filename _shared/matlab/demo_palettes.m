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
W = S.textW; rh = 1.55; top = 0.9; H = top + n * rh + 0.1;
[fig, ax] = canvas(W, H);
roles = {'1 main', '2 accent', '3 green', '4 purple', '5 earth', '6 extra'};
x0 = 5.3; sw = 1.22; gap = 0.1;
for j = 1:6
    txt(ax, x0 + (j - 1) * (sw + gap) + sw / 2, 0.55, roles{j}, 'FontSize', 6.5, 'Color', c.greyDark, ...
        'HorizontalAlignment', 'center');
end
txt(ax, 14.95, 0.55, 'in use', 'FontSize', 6.5, 'Color', c.greyDark, 'HorizontalAlignment', 'center');
t = linspace(0, 1, 30);
for i = 1:n
    P = kit_palette(names{i}); y = top + (i - 1) * rh;
    plot(ax, [0.2 W - 0.2], [y y] - 0.1, '-', 'Color', c.grid, 'LineWidth', 0.5);
    txt(ax, 0.25, y + 0.38, P.title, 'FontSize', 9, 'FontWeight', 'bold', 'Color', c.ink);
    txt(ax, 0.25, y + 0.80, ['''' P.name ''''], 'FontName', 'Courier New', 'FontSize', 6.5, 'Color', c.axis);
    src = P.source; if P.safe, src = [src ' | colour-blind safe']; end
    txt(ax, 0.25, y + 1.14, src, 'FontSize', 6, 'Color', c.greyDark);
    for j = 1:6
        xs = x0 + (j - 1) * (sw + gap);
        patch(ax, xs + [0 sw sw 0], y + 0.12 + [0 0 0.8 0.8], P.cycle(j, :), 'EdgeColor', 'none');
        txt(ax, xs + sw / 2, y + 1.14, ['#' P.hex{j}], 'FontSize', 5.8, 'Color', c.axis, 'HorizontalAlignment', 'center');
    end
    xa = 13.6; wa = 2.7;                                   % three lines and three bars
    for j = 1:3
        yy = y + 0.95 - 0.75 * (0.25 * j + 0.3 * sin(2 * pi * (t + 0.21 * j)) .* (1 - 0.5 * t) + 0.3) / 1.3;
        plot(ax, xa + 0.55 * wa * t, yy, '-', 'Color', P.cycle(j, :), 'LineWidth', 1.3);
    end
    hb = [0.55 0.8 0.4];
    for j = 1:3
        xb = xa + 0.64 * wa + (j - 1) * 0.33;
        patch(ax, xb + [0 0.27 0.27 0], y + 0.98 - [0 0 hb(j) hb(j)], P.cycle(j + 3, :), 'EdgeColor', 'none');
    end
end
save_fig(fig, 'palettes', S);

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
