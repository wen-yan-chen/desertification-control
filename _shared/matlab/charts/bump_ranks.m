function bump_ranks(ax, R, labs, S, varargin)
%BUMP_RANKS Rank of each item (rows of R) over ordered stages (columns).
%   Items in 'highlight' get colour; the rest stay grey.
%   Options: xlabels, highlight (row indices, default all), colors,
%            room (x units reserved on the right for the names)
p = inputParser;
addParameter(p, 'xlabels', {}); addParameter(p, 'highlight', []); addParameter(p, 'colors', S.cycle);
addParameter(p, 'room', 1.3);
parse(p, varargin{:}); o = p.Results; c = S.c;
[n, T] = size(R); if isempty(o.highlight), o.highlight = 1:n; end
style_axes(ax, S, 'none');
s = linspace(0, 1, 24); e = s .^ 2 .* (3 - 2 * s);
order = [setdiff(1:n, o.highlight), o.highlight(:)'];       % coloured lines on top
for i = order
    q = find(o.highlight == i, 1);
    col = c.grid * 0.9; lw = 1.2; tcol = c.greyDark;
    if ~isempty(q), col = o.colors(mod(q - 1, size(o.colors, 1)) + 1, :); lw = 1.9; tcol = col; end
    xx = []; yy = [];
    for t = 1:T - 1
        xx = [xx, t + s]; yy = [yy, R(i, t) + (R(i, t + 1) - R(i, t)) * e]; %#ok<AGROW>
    end
    plot(ax, xx, yy, '-', 'Color', col, 'LineWidth', lw);
    plot(ax, 1:T, R(i, :), 'o', 'MarkerSize', 4.4, 'MarkerFaceColor', col, 'MarkerEdgeColor', 'w', 'LineWidth', 0.7);
    text(ax, T + 0.18, R(i, T), labs{i}, 'FontName', S.font, 'FontSize', S.fs.note - 0.3, 'Color', tcol);
end
set(ax, 'YDir', 'reverse');
xlim(ax, [0.7, T + o.room]); ylim(ax, [0.5 n + 0.5]);
xticks(ax, 1:T); yticks(ax, 1:n);
if ~isempty(o.xlabels), xticklabels(ax, o.xlabels); end
end
