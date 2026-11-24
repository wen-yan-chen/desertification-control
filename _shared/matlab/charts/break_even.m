function xc = break_even(ax, x, cost, gain, S, varargin)
%BREAK_EVEN Two curves with the gain and loss regions shaded and crossings marked.
%   Returns the crossing positions (linear interpolation between samples).
%   Options: names ({'Cost','Revenue'}, written past the right end of each line),
%            fmt (crossing label, '' to hide),
%            room (share of the x range reserved for the names, default 0.42)
p = inputParser;
addParameter(p, 'names', {'Cost', 'Revenue'}); addParameter(p, 'fmt', 'break-even at %.1f');
addParameter(p, 'room', 0.42);
parse(p, varargin{:}); o = p.Results; c = S.c;
x = x(:); cost = cost(:); gain = gain(:); d = gain - cost;
style_axes(ax, S, 'y');
fill(ax, [x; flipud(x)], [max(cost, gain); flipud(cost)], c.vegMid, 'FaceAlpha', 0.2, 'EdgeColor', 'none');
fill(ax, [x; flipud(x)], [cost; flipud(min(cost, gain))], c.limit, 'FaceAlpha', 0.1, 'EdgeColor', 'none');
plot(ax, x, cost, '-', 'Color', c.sand, 'LineWidth', 1.35);
plot(ax, x, gain, '-', 'Color', c.water, 'LineWidth', 1.35);
yr = max([cost; gain]) - min([cost; gain]); xr = x(end) - x(1);
i = find(d(1:end - 1) .* d(2:end) < 0);
xc = x(i) + (x(i + 1) - x(i)) .* d(i) ./ (d(i) - d(i + 1));
yc = interp1(x, cost, xc);
plot(ax, xc, yc, 'o', 'MarkerSize', 4.6, 'MarkerFaceColor', 'w', 'MarkerEdgeColor', c.ink, 'LineWidth', 0.9);
if ~isempty(o.fmt)
    for k = 1:numel(xc)                                 % above both curves, on the side with more room
        ha = 'right'; s = -1; if xc(k) < x(1) + 0.45 * xr, ha = 'left'; s = 1; end
        yt = max(interp1(x, cost, xc(k) + s * 0.25 * xr, 'linear', 'extrap'), ...
                 interp1(x, gain, xc(k) + s * 0.25 * xr, 'linear', 'extrap'));
        text(ax, xc(k) + s * 0.03 * xr, max(yc(k), yt) + 0.05 * yr, sprintf(o.fmt, xc(k)), 'FontName', S.font, ...
            'FontSize', S.fs.note - 0.3, 'Color', c.ink, 'HorizontalAlignment', ha, 'VerticalAlignment', 'bottom');
    end
end
ye = [cost(end) gain(end)]; col = [c.sand; c.water];
if abs(diff(ye)) < 0.09 * yr, ye = mean(ye) + 0.045 * yr * sign(diff(ye) + eps) * [-1 1]; end
for q = 1:2
    text(ax, x(end) + 0.03 * xr, ye(q), o.names{q}, 'FontName', S.font, 'FontSize', S.fs.note - 0.3, ...
        'Color', col(q, :), 'BackgroundColor', 'w', 'Margin', 0.5);
end
xlim(ax, [x(1), x(end) + o.room * xr]); ylim(ax, [min([cost; gain]) - 0.05 * yr, max([cost; gain]) + 0.08 * yr]);
end
