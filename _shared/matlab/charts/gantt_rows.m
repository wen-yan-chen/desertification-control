function gantt_rows(ax, t0, t1, labs, S, varargin)
%GANTT_ROWS Task bars from start t0 to finish t1, first task on top.
%   Options: groups (colour index per task), colors, names (legend, one per
%            group), deadline (x of a red dashed line), deadlinelabel
p = inputParser;
addParameter(p, 'groups', []); addParameter(p, 'colors', S.cycle); addParameter(p, 'names', {});
addParameter(p, 'deadline', []); addParameter(p, 'deadlinelabel', 'deadline');
parse(p, varargin{:}); o = p.Results; c = S.c;
n = numel(t0); yv = n:-1:1; if isempty(o.groups), o.groups = ones(1, n); end
style_axes(ax, S, 'x');
ng = max(o.groups); h = gobjects(1, ng);
for k = 1:n
    g = o.groups(k);
    h(g) = patch(ax, [t0(k) t1(k) t1(k) t0(k)], yv(k) + 0.3 * [-1 -1 1 1], o.colors(g, :), 'EdgeColor', 'none');
end
xl = [min(t0) max(t1)]; if ~isempty(o.deadline), xl(2) = max(xl(2), o.deadline); end
xl = xl + 0.04 * diff(xl) * [-1 1];
if ~isempty(o.deadline)
    plot(ax, o.deadline * [1 1], [0.4 n + 0.6], '--', 'Color', c.limit, 'LineWidth', 0.9);
    text(ax, o.deadline - 0.02 * diff(xl), n + 0.5, o.deadlinelabel, 'FontName', S.font, ...
        'FontSize', S.fs.note - 0.5, 'Color', c.limit, 'HorizontalAlignment', 'right', 'VerticalAlignment', 'top');
end
top = n + 0.6; if ~isempty(o.names), top = n + 1.6; end   % headroom for the legend
xlim(ax, xl); ylim(ax, [0.4 top]);
yticks(ax, 1:n); yticklabels(ax, flip(string(labs))); ax.YAxis.TickLength = [0 0];
if ~isempty(o.names), kit_legend(ax, h, o.names, S, 'north', ng); end
end
