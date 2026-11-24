function cb = heatmap_grid(ax, Z, S, varargin)
%HEATMAP_GRID Annotated heatmap for a small matrix; NaN cells are left grey.
%   Row 1 is drawn on top. Use cmap 'div' with a symmetric clim for
%   correlations or deviations, 'seq' for one-sided quantities.
%   Options: xlabels, ylabels, fmt ('' hides the numbers), clim, cmap (ramp
%            name or n-by-3), cbar (colour bar label, '' for no bar),
%            mark ([row col] cells outlined in ink)
p = inputParser;
addParameter(p, 'xlabels', {}); addParameter(p, 'ylabels', {}); addParameter(p, 'fmt', '%.0f');
addParameter(p, 'clim', [min(Z(:)) max(Z(:))]); addParameter(p, 'cmap', 'seq');
addParameter(p, 'cbar', ''); addParameter(p, 'mark', []);
parse(p, varargin{:}); o = p.Results; c = S.c;
[ny, nx] = size(Z);
cm = o.cmap; if ischar(cm) || isstring(cm), cm = kit_cmap(S, char(cm), 128); end
style_axes(ax, S, 'none');
fs = S.fs.note - 0.8; if max(nx, ny) > 8, fs = S.fs.note - 1.8; end
for i = 1:ny
    for j = 1:nx
        v = Z(i, j);
        if isnan(v)
            col = c.grid; str = char(8211);
        else
            f = min(1, max(0, (v - o.clim(1)) / max(eps, diff(o.clim))));
            col = cm(max(1, round(1 + f * (size(cm, 1) - 1))), :); str = strrep(sprintf(o.fmt, v), '-', char(8722));
        end
        patch(ax, j + 0.5 * [-1 1 1 -1], i + 0.5 * [-1 -1 1 1], col, 'EdgeColor', 'w', 'LineWidth', 0.7);
        if ~isempty(o.fmt)
            text(ax, j, i, str, 'FontName', S.font, 'FontSize', fs, 'Color', ink_on(col, S), ...
                'HorizontalAlignment', 'center');
        end
    end
end
for q = 1:size(o.mark, 1)
    r = o.mark(q, :);
    plot(ax, r(2) + 0.5 * [-1 1 1 -1 -1], r(1) + 0.5 * [-1 -1 1 1 -1], '-', 'Color', c.ink, 'LineWidth', 1.1);
end
set(ax, 'YDir', 'reverse', 'TickLength', [0 0], 'CLim', o.clim, 'Colormap', cm);
xlim(ax, [0.5 nx + 0.5]); ylim(ax, [0.5 ny + 0.5]);
xticks(ax, 1:nx); yticks(ax, 1:ny);
if ~isempty(o.xlabels), xticklabels(ax, o.xlabels); end
if ~isempty(o.ylabels), yticklabels(ax, o.ylabels); end
cb = [];
if ~isempty(o.cbar)
    cb = colorbar(ax);
    set(cb, 'FontName', S.font, 'FontSize', S.fs.note - 0.5, 'TickDirection', 'out', ...
        'LineWidth', 0.5, 'Color', c.axis, 'Box', 'off');
    cb.Label.String = o.cbar; cb.Label.FontSize = S.fs.note; cb.Label.Color = c.ink;
end
end
