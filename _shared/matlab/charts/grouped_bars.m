function h = grouped_bars(ax, M, labs, S, varargin)
%GROUPED_BARS Vertical bars, one group per row of M and one series per column.
%   Options: names (legend), colors (k-by-3), fmt (value label, '' to hide)
p = inputParser;
addParameter(p, 'names', {}); addParameter(p, 'colors', S.cycle); addParameter(p, 'fmt', '%.0f');
parse(p, varargin{:}); o = p.Results; c = S.c;
[n, k] = size(M); w = 0.78 / k;
style_axes(ax, S, 'y');
h = gobjects(1, k);
for j = 1:k
    xc = (1:n) + (j - (k + 1) / 2) * w;
    for i = 1:n
        h(j) = patch(ax, xc(i) + 0.46 * w * [-1 1 1 -1], [0 0 M(i, j) M(i, j)], o.colors(j, :), 'EdgeColor', 'none');
        if ~isempty(o.fmt)
            text(ax, xc(i), M(i, j), sprintf(o.fmt, M(i, j)), 'FontName', S.font, 'FontSize', S.fs.note - 1, ...
                'Color', c.ink, 'HorizontalAlignment', 'center', 'VerticalAlignment', 'bottom');
        end
    end
end
top = 1.12; if ~isempty(o.names), top = 1.36; end          % headroom for the legend
xlim(ax, [0.45 n + 0.55]); ylim(ax, [min(0, min(M(:))) top * max(M(:))]);
xticks(ax, 1:n); xticklabels(ax, labs); ax.XAxis.TickLength = [0 0];
if ~isempty(o.names), kit_legend(ax, h, o.names, S, 'north', k); end
end
