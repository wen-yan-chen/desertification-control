function fit_equal(ax)
%FIT_EQUAL Widen the limits of an equal-aspect axes until it fills its slot.
%   radar_chart, donut_share and network_graph use equal data units, which
%   shrinks the plot box and moves the panel title with it. Call this once
%   the layout is final so the title lines up with the neighbouring panels.
ax.DataAspectRatioMode = 'auto';            % release the constraint to measure the slot
drawnow;
pos = getpixelposition(ax); r = pos(3) / pos(4);
xl = xlim(ax); yl = ylim(ax);
if diff(xl) / diff(yl) < r
    xl = mean(xl) + diff(yl) * r / 2 * [-1 1];
else
    yl = mean(yl) + diff(xl) / r / 2 * [-1 1];
end
xlim(ax, xl); ylim(ax, yl);
ax.DataAspectRatio = [1 1 1];
end
