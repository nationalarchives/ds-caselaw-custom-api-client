<?xml version="1.0"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:uk='https://caselaw.nationalarchives.gov.uk/akn'
    xmlns:akn='http://docs.oasis-open.org/legaldocml/ns/akn/3.0'>

    <xsl:param name="dog" />
    <xsl:param name="cat" />
    <xsl:output method="xml" indent="yes" />

    <xsl:template match="@* | node()">
        <xsl:copy>
            <xsl:apply-templates select="@* | node()" />
        </xsl:copy>
    </xsl:template>

    <xsl:template match="akn:text/text()"><xsl:copy-of select="$cat" /></xsl:template>

    <xsl:template match="akn:attribute">
        <akn:attribute>
            <xsl:attribute name="attribute">
                <xsl:value-of select="$dog" />
            </xsl:attribute>
        </akn:attribute>
    </xsl:template>

</xsl:stylesheet>
