function h = radar_chart(ax, V, labels, S, varargin)
%RADAR_CHART Profiles on shared axes; rows of V are series, columns are axes.
%   Scale every axis to the same range first (0 to rmax, larger is better).
%   Options: names (legend), rmax (default 1), rings, colors, ringfmt
p = inputParser;
addParameter(p, 'names', {}); addParameter(p, 'rmax', 1); addParameter(p, 'rings', 4);
addParameter(p, 'colors', S.cycle); addParameter(p, 'ringfmt', '%.2g');
parse(p, varargin{:}); o = p.Results; c = S.c;
[m, n] = size(V); th = pi / 2 - (0:n - 1) * 2 * pi / n; loop = [1:n 1];
hold(ax, 'on'); axis(ax, 'equal'); axis(ax, 'off');
for k = 1:o.rings
    r = k / o.rings; col = c.grid * 0.93; lw = 0.5;
    if k == o.rings, col = c.grey; lw = 0.7; end
    plot(ax, r * cos(th(loop)), r * sin(th(loop)), '-', 'Color', col, 'LineWidth', lw);
end
for k = 1:n
    plot(ax, [0 cos(th(k))], [0 sin(th(k))], '-', 'Color', c.grid * 0.93, 'LineWidth', 0.5);
    ha = 'center'; va = 'middle';
    if cos(th(k)) > 0.2, ha = 'left'; elseif cos(th(k)) < -0.2, ha = 'right'; end
    if sin(th(k)) > 0.5, va = 'bottom'; elseif sin(th(k)) < -0.5, va = 'top'; end
    text(ax, 1.1 * cos(th(k)), 1.1 * sin(th(k)), labels{k}, 'FontName', S.font, 'FontSize', S.fs.note, ...
        'Color', c.ink, 'HorizontalAlignment', ha, 'VerticalAlignment', va);
end
h = gobjects(1, m); mk = {'o', 's', 'd', '^'};
for i = 1:m
    r = V(i, loop) / o.rmax; col = o.colors(i, :);
    patch(ax, r .* cos(th(loop)), r .* sin(th(loop)), col, 'FaceAlpha', 0.13, 'EdgeColor', 'none');
    h(i) = plot(ax, r .* cos(th(loop)), r .* sin(th(loop)), ['-' mk{mod(i - 1, 4) + 1}], 'Color', col, ...
        'LineWidth', 1.2, 'MarkerSize', 3.2, 'MarkerFaceColor', col, 'MarkerEdgeColor', 'w');
end
a = (th(1) + th(2)) / 2; rr = cos(pi / n);               % ring values between the first two spokes
for k = 1:o.rings - 1
    text(ax, k / o.rings * rr * cos(a), k / o.rings * rr * sin(a), sprintf(o.ringfmt, k / o.rings * o.rmax), ...
        'FontName', S.font, 'FontSize', S.fs.note - 1.8, 'Color', c.greyDark, 'HorizontalAlignment', 'center', ...
        'BackgroundColor', 'w', 'Margin', 0.2);
end
bot = -1.3; if ~isempty(o.names), bot = -2.05; end        % room for the legend
xlim(ax, [-1.5 1.5]); ylim(ax, [bot 1.3]);
if ~isempty(o.names), kit_legend(ax, h, o.names, S, 'south', m); end
end
