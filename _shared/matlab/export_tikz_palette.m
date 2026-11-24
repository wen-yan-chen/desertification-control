function export_tikz_palette(S, file)
%EXPORT_TIKZ_PALETTE Write the active palette as a TikZ colour file.
%   export_tikz_palette(paper_style('palette', 'npg'), 'paper_palette.tex')
%   The file defines the same colour names as tikz/paper_palette.tex, so the
%   TikZ diagrams pick up the palette of the MATLAB figures unchanged.
c = S.c; mix = @(a, t) a * (1 - t) + t;
pvLight = mix(c.pvDark, 0.88); plumLight = mix(c.plum, 0.90);
if strcmp(S.palette, 'oasis'), pvLight = hex2rgb('FDF1E3'); plumLight = hex2rgb('F2EBF3'); end
names = {'pWater', c.water; 'pWaterMid', c.waterMid; 'pWaterLight', c.waterLight; 'pTeal', c.teal; ...
    'pVeg', c.veg; 'pVegMid', c.vegMid; 'pVegLight', c.vegLight; 'pSand', c.sand; 'pSandLight', c.sandLight; ...
    'pAccent', c.accent; 'pPV', c.pvDark; 'pPVLight', pvLight; 'pPlum', c.plum; 'pPlumLight', plumLight; ...
    'pLimit', c.limit; 'pInk', c.ink; 'pAxis', c.axis; 'pGrey', c.grey; 'pGreyDark', c.greyDark; 'pGrid', c.grid};
fid = fopen(file, 'w');
fprintf(fid, '%% Shared colours for the TikZ schematics, palette "%s".\n', S.palette);
fprintf(fid, '%% Written by export_tikz_palette.m; same roles as matlab/paper_style.m.\n');
for k = 1:size(names, 1)
    fprintf(fid, '\\definecolor{%s}{HTML}{%02X%02X%02X}\n', names{k, 1}, round(255 * names{k, 2}));
end
fclose(fid);
end
