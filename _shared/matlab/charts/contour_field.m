function cb = contour_field(ax, X, Y, Z, S, varargin)
%CONTOUR_FIELD Filled contours of a response over two inputs, with labelled levels.
%   Options: levels (count or vector), cmap (ramp name), mark ([x y] of a star,
%            e.g. the optimum), cbar (colour bar label, '' for no bar)
p = inputParser;
addParameter(p, 'levels', 8); addParameter(p, 'cmap', 'seq'); addParameter(p, 'mark', []);
addParameter(p, 'cbar', '');
parse(p, varargin{:}); o = p.Results; c = S.c;
style_axes(ax, S, 'none');
[C, h] = contourf(ax, X, Y, Z, o.levels, 'LineColor', 'w', 'LineWidth', 0.5);
clabel(C, h, 'FontName', S.font, 'FontSize', S.fs.note - 1.5, 'Color', c.ink, 'LabelSpacing', 500);
colormap(ax, kit_cmap(S, o.cmap, 128));
if ~isempty(o.mark)
    plot(ax, o.mark(1), o.mark(2), 'p', 'MarkerSize', 9.5, 'MarkerFaceColor', c.accent, ...
        'MarkerEdgeColor', c.ink, 'LineWidth', 0.6);
end
ax.Layer = 'top';
xlim(ax, [min(X(:)) max(X(:))]); ylim(ax, [min(Y(:)) max(Y(:))]);
cb = [];
if ~isempty(o.cbar)
    cb = colorbar(ax);
    set(cb, 'FontName', S.font, 'FontSize', S.fs.note - 0.5, 'TickDirection', 'out', ...
        'LineWidth', 0.5, 'Color', c.axis, 'Box', 'off');
    cb.Label.String = o.cbar; cb.Label.FontSize = S.fs.note; cb.Label.Color = c.ink;
end
end
