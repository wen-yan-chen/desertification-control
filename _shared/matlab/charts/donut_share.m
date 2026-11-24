function donut_share(ax, vals, labs, S, varargin)
%DONUT_SHARE Shares of one total, clockwise from the top, named outside the ring.
%   Keep it to six parts or fewer; use stacked_bars to compare several totals.
%   Options: colors, center (text in the hole), fmt (share label)
p = inputParser;
addParameter(p, 'colors', S.cycle); addParameter(p, 'center', ''); addParameter(p, 'fmt', '%.0f%%');
parse(p, varargin{:}); o = p.Results; c = S.c;
sh = vals(:)' / sum(vals); edge = pi / 2 - 2 * pi * [0 cumsum(sh)]; r0 = 0.58; n = numel(sh);
hold(ax, 'on'); axis(ax, 'equal'); axis(ax, 'off');
mid = (edge(1:end - 1) + edge(2:end)) / 2; ly = 1.18 * sin(mid); right = cos(mid) >= 0;
for side = [true false]                                 % keep the names on each side apart
    k = find(right == side); [~, ord] = sort(ly(k), 'descend'); k = k(ord);
    for q = 2:numel(k), ly(k(q)) = min(ly(k(q)), ly(k(q - 1)) - 0.3); end
end
for k = 1:n
    t = linspace(edge(k), edge(k + 1), max(8, ceil(120 * sh(k))));
    patch(ax, [cos(t) r0 * cos(fliplr(t))], [sin(t) r0 * sin(fliplr(t))], o.colors(k, :), ...
        'EdgeColor', 'w', 'LineWidth', 1);
    sx = 2 * right(k) - 1; ha = 'left'; if ~right(k), ha = 'right'; end
    lx = sx * max(1.12, sqrt(max(0, 1.18 ^ 2 - ly(k) ^ 2)));
    plot(ax, [1.02 * cos(mid(k)), lx - 0.03 * sx], [1.02 * sin(mid(k)), ly(k)], '-', 'Color', c.grey, 'LineWidth', 0.5);
    text(ax, lx, ly(k), [labs{k} ' \bf' sprintf(o.fmt, 100 * sh(k))], 'FontName', S.font, ...
        'FontSize', S.fs.note - 0.3, 'Color', c.ink, 'HorizontalAlignment', ha);
end
if ~isempty(o.center)
    text(ax, 0, 0, o.center, 'FontName', S.font, 'FontSize', S.fs.note + 0.5, 'FontWeight', 'bold', ...
        'Color', c.ink, 'HorizontalAlignment', 'center');
end
xlim(ax, [-2.5 2.5]); ylim(ax, [-1.4 1.4]);
end
