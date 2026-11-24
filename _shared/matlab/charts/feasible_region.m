function [V, xbest] = feasible_region(ax, A, b, xl, yl, S, varargin)
%FEASIBLE_REGION Region A*[x; y] <= b inside the box xl-by-yl, with its constraint lines.
%   Returns the polygon vertices V and, if an objective is given, the best vertex.
%   Options: names (one per constraint, for the legend),
%            objective ([cx cy], maximised over the region), legend (location)
p = inputParser;
addParameter(p, 'names', {}); addParameter(p, 'objective', []); addParameter(p, 'legend', 'northeast');
parse(p, varargin{:}); o = p.Results; c = S.c;
V = [xl(1) yl(1); xl(2) yl(1); xl(2) yl(2); xl(1) yl(2)];
for i = 1:size(A, 1)                                   % clip the box by each half-plane
    W = zeros(0, 2); m = size(V, 1);
    for k = 1:m
        P = V(k, :); Q = V(mod(k, m) + 1, :);
        fp = A(i, :) * P' - b(i); fq = A(i, :) * Q' - b(i);
        if fp <= 0, W(end + 1, :) = P; end %#ok<AGROW>
        if fp * fq < 0, W(end + 1, :) = P + (Q - P) * fp / (fp - fq); end %#ok<AGROW>
    end
    V = W;
end
style_axes(ax, S, 'xy');
patch(ax, V(:, 1), V(:, 2), c.vegMid, 'FaceAlpha', 0.22, 'EdgeColor', 'none');
col = [c.water; c.accent; c.plum; c.sand; c.teal; c.greyDark];
h = gobjects(1, size(A, 1));
for i = 1:size(A, 1)
    if abs(A(i, 2)) > 1e-12
        xx = xl; yy = (b(i) - A(i, 1) * xx) / A(i, 2);
    else
        xx = b(i) / A(i, 1) * [1 1]; yy = yl;
    end
    h(i) = plot(ax, xx, yy, '-', 'Color', col(mod(i - 1, 6) + 1, :), 'LineWidth', 1.1);
end
xbest = [];
if ~isempty(o.objective)
    [zb, k] = max(V * o.objective(:)); xbest = V(k, :);
    if abs(o.objective(2)) > 1e-12
        h(end + 1) = plot(ax, xl, (zb - o.objective(1) * xl) / o.objective(2), '--', 'Color', c.greyDark, 'LineWidth', 0.8);
        o.names{end + 1} = 'best objective';
    end
    plot(ax, xbest(1), xbest(2), 'p', 'MarkerSize', 9.5, 'MarkerFaceColor', c.accent, ...
        'MarkerEdgeColor', c.ink, 'LineWidth', 0.6);
end
xlim(ax, xl); ylim(ax, yl);
if ~isempty(o.names) && ~isempty(o.legend)
    lg = kit_legend(ax, h, o.names, S, o.legend);
    set(lg, 'Box', 'on', 'Color', 'w', 'EdgeColor', 'none');      % lines run behind it
end
end
