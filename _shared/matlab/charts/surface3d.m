function surface3d(ax, X, Y, Z, S, varargin)
%SURFACE3D Smooth response surface with its contours projected on the floor.
%   Use only for a continuous function sampled on a full grid; a small
%   discrete grid belongs in bars3d or heatmap_grid.
%   Options: cmap (ramp name), view ([az el]), mark ([x y z] of a star)
p = inputParser;
addParameter(p, 'cmap', 'seq'); addParameter(p, 'view', [-38 28]); addParameter(p, 'mark', []);
parse(p, varargin{:}); o = p.Results; c = S.c;
style_axes(ax, S, 'xy');
set(ax, 'ZGrid', 'on', 'ZColor', c.axis, 'ZMinorTick', 'off', 'TickLength', [0.015 0.015]);
ax.ZLabel.FontSize = S.fs.label; ax.ZLabel.Color = c.ink;
zr = max(Z(:)) - min(Z(:)); z0 = min(Z(:)) - 0.45 * zr;
[~, hc] = contour(ax, X, Y, Z, 8, 'LineWidth', 0.6);
hc.ContourZLevel = z0;
surf(ax, X, Y, Z, 'EdgeColor', c.axis, 'EdgeAlpha', 0.22, 'LineWidth', 0.3, 'FaceAlpha', 0.96);
colormap(ax, kit_cmap(S, o.cmap, 128));
if ~isempty(o.mark)
    plot3(ax, o.mark(1), o.mark(2), o.mark(3), 'p', 'MarkerSize', 9.5, 'MarkerFaceColor', c.accent, ...
        'MarkerEdgeColor', c.ink, 'LineWidth', 0.6);
end
xlim(ax, [min(X(:)) max(X(:))]); ylim(ax, [min(Y(:)) max(Y(:))]); zlim(ax, [z0 max(Z(:)) + 0.05 * zr]);
view(ax, o.view(1), o.view(2));
end
