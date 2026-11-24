function bars3d(ax, Z, S, varargin)
%BARS3D 3-D bars on a small discrete grid, drawn as shaded patches.
%   bars3d(ax, Z, S, 'labels', L, 'clim', [lo hi], 'highlight', [row col], ...)
%   Z(i, j) is the bar height at y = i (row 1 at the front), x = j.
%   Bars are drawn back to front for the chosen view, so the vector PDF needs
%   no depth sorting. Colour repeats height on the warm-to-teal paper ramp.
%   Options
%     labels     cell array like Z, text above each bar (TeX), default none
%     clim       heights mapped to the two ends of the ramp (default: data range)
%     highlight  [row col] of one bar to outline in ink (e.g. the baseline)
%     view       [az el], default [28 32]
%     width      half-width of a bar in grid units, default 0.21
%     zmax       upper z limit, default 1.25 * max(Z)
%     gap        label offset above the bar top, default 5% of zmax
%   Set tick labels, axis labels and the title after the call.
p = inputParser;
addParameter(p, 'labels', {});
addParameter(p, 'clim', [min(Z(:)) max(Z(:))]);
addParameter(p, 'highlight', []);
addParameter(p, 'view', [28 32]);
addParameter(p, 'width', 0.21);
addParameter(p, 'zmax', 1.25 * max(Z(:)));
addParameter(p, 'gap', []);
parse(p, varargin{:});
o = p.Results; c = S.c;
if isempty(o.gap), o.gap = 0.05 * o.zmax; end
[ny, nx] = size(Z);

style_axes(ax, S, 'xy');
set(ax, 'ZGrid', 'on', 'ZColor', c.axis, 'ZMinorTick', 'off', 'Projection', 'orthographic', ...
    'TickLength', [0.015 0.015]);
ax.ZLabel.FontSize = S.fs.label; ax.ZLabel.Color = c.ink;

anchors = [c.limit; c.accent; c.sandLight; c.vegMid; c.water];
cmap = interp1(linspace(0, 1, size(anchors, 1)), anchors, linspace(0, 1, 64));

[X, Y] = meshgrid(1:nx, 1:ny);
depth = X * sind(o.view(1)) - Y * cosd(o.view(1));
[~, ord] = sort(depth(:), 'ascend');
w = o.width;
for k = ord'
    x0 = X(k); y0 = Y(k); h = Z(k);
    frac = min(1, max(0, (h - o.clim(1)) / max(eps, o.clim(2) - o.clim(1))));
    f = cmap(max(1, round(1 + frac * 63)), :);
    ecol = 0.55 * f + 0.45 * c.axis; lw = 0.42;
    if isequal([y0 x0], o.highlight), ecol = c.ink; lw = 0.65; end
    patch(ax, [x0-w x0+w x0+w x0-w], [y0-w y0-w y0-w y0-w], [0 0 h h], f * 0.92, ...
        'EdgeColor', ecol, 'LineWidth', lw, 'HandleVisibility', 'off');
    patch(ax, [x0+w x0+w x0+w x0+w], [y0-w y0+w y0+w y0-w], [0 0 h h], f * 0.76, ...
        'EdgeColor', ecol, 'LineWidth', lw, 'HandleVisibility', 'off');
    patch(ax, [x0-w x0+w x0+w x0-w], [y0-w y0-w y0+w y0+w], [h h h h], min(1, f * 1.04 + 0.05), ...
        'EdgeColor', ecol, 'LineWidth', lw, 'HandleVisibility', 'off');
end
if ~isempty(o.labels)
    for k = 1:numel(Z)
        text(ax, X(k), Y(k), Z(k) + o.gap, o.labels{k}, 'FontName', S.font, ...
            'FontSize', S.fs.note - 1.1, 'Color', c.ink, 'HorizontalAlignment', 'center', ...
            'VerticalAlignment', 'bottom', 'Interpreter', 'tex');
    end
end
xlim(ax, [0.45 nx + 0.55]); ylim(ax, [0.45 ny + 0.55]); zlim(ax, [0 o.zmax]);
xticks(ax, 1:nx); yticks(ax, 1:ny);
view(ax, o.view(1), o.view(2));
end
