function h = band_lines(ax, x, Y, S, varargin)
%BAND_LINES Scenario paths with range bands, named at the right end of each line.
%   Columns of Y are series; lo and hi (same size) give the band of each.
%   Options: lo, hi, names, colors, styles (cell of line styles),
%            room (share of the x range reserved for the names, default 0.3)
p = inputParser;
addParameter(p, 'lo', []); addParameter(p, 'hi', []); addParameter(p, 'names', {});
addParameter(p, 'colors', S.cycle); addParameter(p, 'styles', {}); addParameter(p, 'room', 0.3);
parse(p, varargin{:}); o = p.Results;
x = x(:); k = size(Y, 2);
style_axes(ax, S, 'y');
if ~isempty(o.lo)
    for j = 1:k
        fill(ax, [x; flipud(x)], [o.lo(:, j); flipud(o.hi(:, j))], o.colors(j, :), ...
            'FaceAlpha', 0.15, 'EdgeColor', 'none');
    end
end
h = gobjects(1, k);
for j = 1:k
    ls = '-'; if numel(o.styles) >= j, ls = o.styles{j}; end
    h(j) = plot(ax, x, Y(:, j), ls, 'Color', o.colors(j, :), 'LineWidth', 1.35);
end
allv = [Y(:); o.lo(:); o.hi(:)]; yl = [min(allv) max(allv)]; yl = yl + 0.06 * diff(yl) * [-1 1];
xr = x(end) - x(1);
if ~isempty(o.names)
    ye = Y(end, :); [~, ord] = sort(ye); gap = 0.075 * diff(yl); yt = ye(ord);
    for j = 2:k, yt(j) = max(yt(j), yt(j - 1) + gap); end        % keep names apart
    for j = 1:k
        text(ax, x(end) + 0.03 * xr, yt(j), o.names{ord(j)}, 'FontName', S.font, ...
            'FontSize', S.fs.note - 0.3, 'Color', o.colors(ord(j), :), 'BackgroundColor', 'w', 'Margin', 0.5);
    end
    xlim(ax, [x(1), x(end) + o.room * xr]);
else
    xlim(ax, [x(1) x(end)]);
end
ylim(ax, yl);
end
