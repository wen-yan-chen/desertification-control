function cm = kit_cmap(S, name, n)
%KIT_CMAP Colour ramps built from the paper palette.
%   'seq'   white to deep teal, for one-sided quantities
%   'warm'  cream to red, for pressure or risk
%   'green' pale to dark green, for cover or benefit
%   'div'   orange - white - teal, for deviations from a meaningful centre
%   'ramp'  red - orange - cream - green - teal, short to long (as in bars3d)
%   The five above follow the active palette. Fixed, perceptually ordered maps:
%   'viridis', 'cividis' (matplotlib; both read in greyscale and are
%   colour-blind safe), 'ylgnbu' (sequential) and 'rdbu' (diverging), both ColorBrewer.
if nargin < 3, n = 64; end
c = S.c;
switch name
    case 'seq',   a = [0.97 0.98 0.99; c.waterLight; c.waterMid; c.water];
    case 'warm',  a = [c.sandLight; c.accent; c.limit];
    case 'green', a = [c.vegLight; c.vegMid; c.veg];
    case 'div',   a = [c.pvDark; c.accent; c.sandLight; 1 1 1; c.waterLight; c.waterMid; c.water];
    case 'ramp',  a = [c.limit; c.accent; c.sandLight; c.vegMid; c.water];
    case 'viridis', a = hexs({'440154','443A83','31688E','21918C','35B779','90D743','FDE725'});
    case 'cividis', a = hexs({'00224E','2B406D','575D6D','7D7C78','A59C74','D2C060','FEE838'});
    case 'ylgnbu',  a = hexs({'FFFFD9','EDF8B1','C7E9B4','7FCDBB','41B6C4','1D91C0','225EA8','253494','081D58'});
    case 'rdbu',    a = hexs({'B2182B','D6604D','F4A582','FDDBC7','F7F7F7','D1E5F0','92C5DE','4393C3','2166AC'});
    otherwise, error('kit_cmap:name', 'Unknown ramp "%s".', name);
end
cm = interp1(linspace(0, 1, size(a, 1)), a, linspace(0, 1, n));
end

function a = hexs(h)
a = cell2mat(cellfun(@hex2rgb, h(:), 'UniformOutput', false));
end
