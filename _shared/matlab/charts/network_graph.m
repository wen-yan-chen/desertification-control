function network_graph(ax, A, S, varargin)
%NETWORK_GRAPH Node-link diagram of a symmetric weight matrix A.
%   Edge width follows the weight, node size the weighted degree.
%   Options: xy (n-by-2 positions; a circle if omitted), labels,
%            groups (colour index per node), colors
p = inputParser;
addParameter(p, 'xy', []); addParameter(p, 'labels', {}); addParameter(p, 'groups', []);
addParameter(p, 'colors', S.cycle);
parse(p, varargin{:}); o = p.Results; c = S.c;
n = size(A, 1); A = max(A, A');
if isempty(o.xy), t = pi / 2 - (0:n - 1)' * 2 * pi / n; o.xy = [cos(t) sin(t)]; end
if isempty(o.groups), o.groups = ones(n, 1); end
xy = o.xy; ctr = mean(xy, 1); deg = sum(A, 2); wmax = max(A(:));
hold(ax, 'on'); axis(ax, 'equal'); axis(ax, 'off');
for i = 1:n
    for j = i + 1:n
        if A(i, j) > 0
            plot(ax, xy([i j], 1), xy([i j], 2), '-', 'Color', c.grey, 'LineWidth', 0.4 + 2.4 * A(i, j) / wmax);
        end
    end
end
span = max(max(xy) - min(xy));
for i = 1:n
    ms = 5 + 7 * deg(i) / max(deg);
    plot(ax, xy(i, 1), xy(i, 2), 'o', 'MarkerSize', ms, 'MarkerFaceColor', o.colors(o.groups(i), :), ...
        'MarkerEdgeColor', 'w', 'LineWidth', 0.8);
    if ~isempty(o.labels)
        d = xy(i, :) - ctr; d = d / max(norm(d), eps);
        ha = 'center'; if d(1) > 0.3, ha = 'left'; elseif d(1) < -0.3, ha = 'right'; end
        va = 'middle'; if d(2) > 0.6, va = 'bottom'; elseif d(2) < -0.6, va = 'top'; end
        text(ax, xy(i, 1) + 0.1 * span * d(1), xy(i, 2) + 0.1 * span * d(2), o.labels{i}, 'FontName', S.font, ...
            'FontSize', S.fs.note - 0.3, 'Color', c.ink, 'HorizontalAlignment', ha, 'VerticalAlignment', va);
    end
end
lo = min(xy) - 0.3 * span; hi = max(xy) + 0.3 * span;
xlim(ax, [lo(1) hi(1)]); ylim(ax, [lo(2) hi(2)]);
end
