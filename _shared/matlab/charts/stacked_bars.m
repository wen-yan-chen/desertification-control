function h = stacked_bars(ax, M, labs, S, varargin)
%STACKED_BARS Horizontal stacked bars: rows of M are cases, columns are parts.
%   Pass shares that sum to 100 for a composition chart, or raw amounts.
%   Options: names, colors, fmt, minlabel (smallest labelled part, % of the axis)
p = inputParser;
addParameter(p, 'names', {}); addParameter(p, 'colors', S.cycle); addParameter(p, 'fmt', '%.0f');
addParameter(p, 'minlabel', 9);
parse(p, varargin{:}); o = p.Results;
[n, k] = size(M); yv = n:-1:1; tot = max(sum(M, 2));
style_axes(ax, S, 'x');
h = gobjects(1, k);
for i = 1:n
    left = 0;
    for j = 1:k
        w = M(i, j);
        h(j) = patch(ax, left + [0 w w 0], yv(i) + 0.33 * [-1 -1 1 1], o.colors(j, :), ...
            'EdgeColor', 'w', 'LineWidth', 0.6);
        if w >= o.minlabel / 100 * tot && ~isempty(o.fmt)
            text(ax, left + w / 2, yv(i), sprintf(o.fmt, w), 'FontName', S.font, 'FontSize', S.fs.note - 1, ...
                'Color', ink_on(o.colors(j, :), S), 'HorizontalAlignment', 'center');
        end
        left = left + w;
    end
end
top = n + 0.6; if ~isempty(o.names), top = n + 1.35; end   % headroom for the legend
xlim(ax, [0 tot]); ylim(ax, [0.4 top]);
yticks(ax, 1:n); yticklabels(ax, flip(string(labs))); ax.YAxis.TickLength = [0 0];
if ~isempty(o.names), kit_legend(ax, h, o.names, S, 'north', k); end
end
