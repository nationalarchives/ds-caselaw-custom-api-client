<?xml version="1.0" encoding="utf-8"?>

<xsl:transform xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="2.0"
	xpath-default-namespace="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"
	xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn"
	xmlns:html="http://www.w3.org/1999/xhtml"
	xmlns:math="http://www.w3.org/1998/Math/MathML"
	xmlns:xs="http://www.w3.org/2001/XMLSchema"
	exclude-result-prefixes="uk html math xs">

<xsl:output method="html" encoding="utf-8" indent="no" include-content-type="no" />

<xsl:strip-space elements="*" />
<xsl:preserve-space elements="p block num heading span a courtType date docDate docTitle docketNumber judge lawyer location neutralCitation party role time" />

<xsl:param name="image-prefix" as="xs:string" />

<xsl:function name="uk:link-is-supported" as="xs:boolean">
	<xsl:param name="href" as="attribute()?" />
	<xsl:choose>
		<xsl:when test="$href='#'">
			<xsl:sequence select="false()" />
		</xsl:when>
		<xsl:when test="starts-with($href, '#')">
			<xsl:sequence select="true()" />
		</xsl:when>
		<xsl:when test="starts-with($href, 'https://www.legislation.gov.uk/')">
			<xsl:sequence select="true()" />
		</xsl:when>
		<xsl:when test="starts-with($href, 'http://www.legislation.gov.uk/')">
			<xsl:sequence select="true()" />
		</xsl:when>
		<xsl:when test="starts-with($href, 'https://caselaw.nationalarchives.gov.uk/')">
			<xsl:variable name="components" as="xs:string*" select="tokenize(substring-after($href, 'https://caselaw.nationalarchives.gov.uk/'), '/')" />
			<xsl:choose>
				<xsl:when test="empty($components[3])">
					<xsl:sequence select="false()" />
				</xsl:when>
				<xsl:when test="$components[1] = ('uksc', 'ukpc')">
					<xsl:sequence select="$components[2] ge '2014'" />
				</xsl:when>
				<xsl:when test="$components[1] = ('ewca', 'ewhc')">
					<xsl:sequence select="$components[3] ge '2003'" />
				</xsl:when>
				<xsl:when test="$components[1] = 'ewcop'">
					<xsl:sequence select="$components[2] ge '2009'" />
				</xsl:when>
				<xsl:when test="$components[1] = 'ewfc'">
					<xsl:sequence select="$components[2] ge '2014'" />
				</xsl:when>
				<xsl:when test="$components[1] = 'ukut'">
					<xsl:choose>
						<xsl:when test="$components[2] = 'iac'">
							<xsl:sequence select="$components[3] ge '2010'" />
						</xsl:when>
						<xsl:when test="$components[2] = 'lc'">
							<xsl:sequence select="$components[3] ge '2015'" />
						</xsl:when>
						<xsl:when test="$components[2] = 'tcc'">
							<xsl:sequence select="$components[3] ge '2017'" />
						</xsl:when>
						<xsl:otherwise>
							<xsl:sequence select="false()" />
						</xsl:otherwise>
					</xsl:choose>
				</xsl:when>
				<xsl:otherwise>
					<xsl:sequence select="false()" />
				</xsl:otherwise>
			</xsl:choose>
		</xsl:when>
		<xsl:otherwise>
			<xsl:sequence select="false()" />
		</xsl:otherwise>
	</xsl:choose>
</xsl:function>

<xsl:variable name="doc-id" as="xs:string">
	<xsl:variable name="work-uri" as="xs:string">
		<xsl:sequence select="/akomaNtoso/*/meta/identification/FRBRWork/FRBRthis/@value" />
	</xsl:variable>
	<xsl:variable name="long-form-prefix" as="xs:string" select="'https://caselaw.nationalarchives.gov.uk/id/'" />
	<xsl:choose>
		<xsl:when test="starts-with($work-uri, $long-form-prefix)">
			<xsl:sequence select="substring-after($work-uri, $long-form-prefix)" />
		</xsl:when>
		<xsl:otherwise>
			<xsl:sequence select="$work-uri" />
		</xsl:otherwise>
	</xsl:choose>
</xsl:variable>

<xsl:template match="meta" />

<xsl:template match="judgment">
	<article class="judgment">
		<xsl:apply-templates />
		<xsl:apply-templates select="attachments/attachment/doc[@name=('annex','schedule')]" />
		<xsl:call-template name="footnotes">
			<xsl:with-param name="footnotes" as="element()*">
				<xsl:sequence select="header//authorialNote" />
				<xsl:sequence select="judgmentBody//authorialNote" />
				<xsl:sequence select="attachments/attachment/doc[@name=('annex','schedule')]//authorialNote" />
			</xsl:with-param>
		</xsl:call-template>
		<xsl:apply-templates select="attachments/attachment/doc[not(@name=('annex','schedule'))]" />
	</article>
</xsl:template>

<!-- for press summaries, priority needed to trump attachment template -->
<xsl:template match="/akomaNtoso/doc" priority="1">
	<article class="judgment">
		<xsl:apply-templates />
		<xsl:call-template name="footnotes" />
	</article>
</xsl:template>

<xsl:template match="attachments" />

<xsl:template match="coverPage | header | preface">
	<header class="judgment-header">
		<xsl:apply-templates />
	</header>
</xsl:template>

<xsl:template match="judgmentBody | doc[@name='pressSummary']/mainBody" priority="1">
	<section class="judgment-body">
		<xsl:apply-templates />
	</section>
</xsl:template>

<xsl:template match="doc[@name=('annex','schedule')]">
	<section>
		<xsl:apply-templates />
	</section>
</xsl:template>

<xsl:template match="doc[not(@name=('annex','schedule'))]">
	<section>
		<xsl:apply-templates />
		<xsl:call-template name="footnotes" />
	</section>
</xsl:template>

<xsl:template match="doc[not(@name=('annex','schedule'))]/mainBody">
	<div>
		<xsl:apply-templates />
	</div>
</xsl:template>

<xsl:template match="decision">
	<xsl:choose>
		<xsl:when test="exists(preceding-sibling::*) or exists(following-sibling::*)">
			<section>
				<xsl:apply-templates />
			</section>
		</xsl:when>
		<xsl:otherwise>
			<xsl:next-match />
		</xsl:otherwise>
	</xsl:choose>
</xsl:template>

<xsl:template match="level">
	<section>
		<xsl:apply-templates select="@eId" />
		<xsl:if test="num | heading">
			<p>
				<xsl:apply-templates select="num | heading" />
			</p>
		</xsl:if>
		<xsl:apply-templates select="* except (num, heading)" />
	</section>
</xsl:template>

<xsl:template match="level/num">
	<span style="display:inline-block;min-width:0.5in">
		<xsl:call-template name="inline" />
	</span>
</xsl:template>

<xsl:template match="paragraph">
	<section class="judgment-body__section">
		<xsl:apply-templates select="@eId" />
		<span class="judgment-body__number">
			<xsl:apply-templates select="num" />
		</span>
		<div>
			<xsl:apply-templates select="* except num" />
		</div>
	</section>
</xsl:template>

<xsl:template match="level/@eId | paragraph/@eId">
	<xsl:attribute name="id">
		<xsl:sequence select="." />
	</xsl:attribute>
</xsl:template>

<xsl:template match="subparagraph">
	<section class="judgment-body__nested-section">
		<span class="judgment-body__number">
			<xsl:apply-templates select="num" />
		</span>
		<div>
			<xsl:apply-templates select="* except num" />
		</div>
	</section>
</xsl:template>

<xsl:template match="paragraph/*/p | subparagraph/*/p">
	<p>
		<xsl:attribute name="class">
			<xsl:choose>
				<xsl:when test="position() = 1">judgment-body__text judgment-body__no-margin-top</xsl:when>
				<xsl:otherwise>judgment-body__text</xsl:otherwise>
			</xsl:choose>
		</xsl:attribute>
		<xsl:call-template name="inline" />
	</p>
</xsl:template>

<!-- <xsl:template match="hcontainer[@name='tableOfContents']" /> -->

<xsl:template match="blockContainer[exists(p)]">
	<xsl:apply-templates select="* except num" />
</xsl:template>

<xsl:template match="blockContainer">
	<xsl:apply-templates />
</xsl:template>

<xsl:template match="blockContainer/num">
	<span style="padding-right:1em">
		<xsl:call-template name="inline" />
	</span>
</xsl:template>

<xsl:template match="blockContainer/p[1]">
	<xsl:param name="class-context" as="element()" tunnel="yes" />
	<p>
		<xsl:if test="exists(ancestor::header)">
			<xsl:variable name="alignment" as="xs:string?" select="uk:extract-alignment(., $class-context)" />
			<xsl:if test="$alignment = ('center', 'right', 'left')">
				<xsl:attribute name="class">
					<xsl:sequence select="concat('judgment-header__pr-', $alignment)" />
				</xsl:attribute>
			</xsl:if>
		</xsl:if>
		<xsl:apply-templates select="../num" />
		<xsl:text> </xsl:text>
		<span>
			<xsl:call-template name="inline" />
		</span>
	</p>
</xsl:template>

<xsl:template match="blockContainer/p[position() gt 1]">
	<xsl:param name="class-context" as="element()" tunnel="yes" />
	<p>
		<xsl:if test="exists(ancestor::header)">
			<xsl:variable name="alignment" as="xs:string?" select="uk:extract-alignment(., $class-context)" />
			<xsl:if test="$alignment = ('center', 'right', 'left')">
				<xsl:attribute name="class">
					<xsl:sequence select="concat('judgment-header__pr-', $alignment)" />
				</xsl:attribute>
			</xsl:if>
		</xsl:if>
		<xsl:call-template name="inline" />
	</p>
</xsl:template>

<!-- quoted structures -->

<xsl:template match="block[@name='embeddedStructure']">
	<xsl:apply-templates />
</xsl:template>

<xsl:template match="embeddedStructure">
	<blockquote>
		<xsl:apply-templates />
	</blockquote>
</xsl:template>


<!-- CSS classes -->

<!-- sets the ancestor document element containing the CSS style for its descendants -->
<!-- if an attachment has its own styles, then that attachment, otherwise the main judgment -->
<!-- priority should be the highest in the transform -->
<xsl:template match="akomaNtoso/* | attachment/*[exists(meta/presentation)]" priority="2">
	<xsl:next-match>
		<xsl:with-param name="class-context" select="." tunnel="yes" />
	</xsl:next-match>
</xsl:template>

<!-- a data structure containing all of the CSS properties, divided by selector and property name -->
<!-- the keys that follow are designed for this structure -->
<xsl:variable name="all-classes-parsed" as="document-node()">
	<xsl:document>
		<uk:classes>
			<xsl:for-each select="(/akomaNtoso/*, /akomaNtoso/*/attachments/attachment/*)[exists(meta/presentation)]">
				<xsl:variable name="root-key" select="generate-id(.)" />
				<uk:classes key="{ $root-key }">
					<xsl:for-each select="tokenize(string(meta/presentation), '\}')[contains(., '{')]">
						<xsl:variable name="selector" select="normalize-space(substring-before(., '{'))" />
						<xsl:variable name="properties" select="normalize-space(substring-after(., '{'))" />
						<uk:class key="{ $selector }">
							<xsl:for-each select="tokenize($properties, ';')[contains(., ':')]">
								<xsl:variable name="property" select="normalize-space(substring-before(., ':'))" />
								<xsl:variable name="value" select="normalize-space(substring-after(., ':'))" />
								<uk:property key="{ $property }" value="{ $value }" />
							</xsl:for-each>
						</uk:class>
					</xsl:for-each>
				</uk:classes>
			</xsl:for-each>
		</uk:classes>
	</xsl:document>
</xsl:variable>

<xsl:key name="classes" match="uk:class" use="concat(../@key, '|', @key)" />

<xsl:key name="class-properties" match="uk:property/@value" use="concat(../../../@key, '|', ../../@key, '|', ../@key)" />

<!-- class property getters -->

<!-- returns the value of the property for the given selector -->
<xsl:function name="uk:get-class-property-1" as="xs:string?">
	<xsl:param name="context" as="element()" />
	<xsl:param name="selector" as="xs:string" />
	<xsl:param name="prop" as="xs:string" />
	<xsl:variable name="key" select="concat(generate-id($context), '|', $selector, '|', $prop)" />
	<xsl:sequence select="key('class-properties', $key, $all-classes-parsed)/string()" />
</xsl:function>

<!-- returns a sequence of key/value pairs, each divided by a colon -->
<xsl:function name="uk:get-all-class-properties" as="xs:string*">
	<xsl:param name="context" as="element()" />
	<xsl:param name="selector" as="xs:string" /> <!-- constructed with 'augment-simple-class-selector' function below -->
	<xsl:variable name="key" select="concat(generate-id($context), '|', $selector)" />
	<xsl:for-each select="key('classes', $key, $all-classes-parsed)/uk:property">
		<xsl:sequence select="concat(@key, ':', @value)" />
	</xsl:for-each>
</xsl:function>

<!-- returns a sequence of key/value pairs, each divided by a colon -->
<xsl:function name="uk:get-inline-class-properties-1" as="xs:string*">
	<xsl:param name="context" as="element()" />
	<xsl:param name="selector" as="xs:string" /> <!-- constructed with 'make-class-selector' function below -->
	<xsl:variable name="key" select="concat(generate-id($context), '|', $selector)" />
	<xsl:for-each select="key('classes', $key, $all-classes-parsed)/uk:property">
		<xsl:if test="string(@key) = $inline-properties">
			<xsl:sequence select="concat(@key, ':', @value)" />
		</xsl:if>
	</xsl:for-each>
</xsl:function>

<!-- helper functions to make selectors, depending on context -->

<!-- adds a prefix to class selector, e.g., #judgment, #main, etc., depending on context -->
<xsl:function name="uk:augment-simple-class-selector" as="xs:string">
	<xsl:param name="context" as="element()" />
	<xsl:param name="class" as="xs:string" /> <!-- starts with a dot -->
	<xsl:choose>
		<!-- the selector for main styles in a judgment is '#judgment .{ClassName}', e.g., '#judgment .ParaLevel1' -->
		<xsl:when test="$context/self::judgment">
			<xsl:sequence select="concat('#judgment ', $class)" />
		</xsl:when>
		<!-- the selector for main styles in a press summary is '#main .{ClassName}', e.g., '#main .ParaLevel1' -->
		<xsl:when test="$context/self::doc[@name='pressSummary']">
			<xsl:sequence select="concat('#main ', $class)" />
		</xsl:when>
		<!-- the selector for attachment styles is '#{type}{num} .{ClassName}', e.g., '#order1 .ParaLevel1' -->
		<xsl:otherwise>
			<xsl:variable name="work-uri" as="xs:string" select="$context/meta/identification/FRBRWork/FRBRthis/@value" />
			<xsl:variable name="uri-components" as="xs:string*" select="tokenize($work-uri, '/')" />
			<xsl:variable name="last-two" as="xs:string*" select="$uri-components[position() >= last()-1]" />
			<xsl:variable name="last-two-combined" as="xs:string" select="string-join($last-two, '')" />
			<xsl:sequence select="concat('#', $last-two-combined, ' ', $class)" />
		</xsl:otherwise>
	</xsl:choose>
</xsl:function>

<xsl:function name="uk:make-class-selector" as="xs:string?">
	<xsl:param name="context" as="element()" />
	<xsl:param name="e" as="element()" />
	<xsl:choose>
		<xsl:when test="empty($e/@class)" />
		<xsl:when test="$doc-id = 'ewhc/ch/2022/1178'">
			<xsl:sequence select="uk:make-class-selector-for-ewhc-ch-2022-1178($context, $e)" />
		</xsl:when>
		<xsl:otherwise>
			<xsl:sequence select="uk:augment-simple-class-selector($context, concat('.', $e/@class))" />
		</xsl:otherwise>
	</xsl:choose>
</xsl:function>

<!-- [2022] EWHC 1178 (Ch) was generated through a manual process and has some exceptions -->
<!-- It contains multiple sets of styles -->
<xsl:function name="uk:make-class-selector-for-ewhc-ch-2022-1178" as="xs:string">
	<xsl:param name="context" as="element()" />
	<xsl:param name="e" as="element()" /> <!-- $e/@class exists -->
	<xsl:variable name="header" as="element()?" select="$e/ancestor::header" />
	<xsl:variable name="decision-id" as="xs:string?" select="$e/ancestor::decision/@eId" />
	<xsl:choose>
		<xsl:when test="$context/self::doc[@name='schedule']">
			<xsl:sequence select="concat('#schedule .', $e/@class)" />
		</xsl:when>
		<xsl:when test="exists($header)">
			<xsl:sequence select="concat('header .', $e/@class, ', #part-a .', $e/@class)" />
		</xsl:when>
		<xsl:when test="exists($decision-id) and $decision-id = 'part-a'"> <!-- same as header -->
			<xsl:sequence select="concat('header .', $e/@class, ', #part-a .', $e/@class)" />
		</xsl:when>
		<xsl:when test="exists($decision-id)">
			<xsl:sequence select="concat('#', $decision-id, ' .', $e/@class)" />
		</xsl:when>
		<xsl:otherwise> <!-- should be impossible -->
			<xsl:sequence select="concat('.', $e/@class)" />
		</xsl:otherwise>
	</xsl:choose>
</xsl:function>

<!-- main class property getters requiring, a source element and a context element -->

<xsl:function name="uk:get-class-property" as="xs:string?">
	<xsl:param name="e" as="element()" />
	<xsl:param name="prop" as="xs:string" />
	<xsl:param name="context" as="element()" />
	<xsl:if test="exists($e/@class)">
		<xsl:variable name="selector" as="xs:string" select="uk:make-class-selector($context, $e)" />
		<xsl:sequence select="uk:get-class-property-1($context, $selector, $prop)" />
	</xsl:if>
</xsl:function>

<xsl:function name="uk:get-inline-class-properties" as="xs:string*">
	<xsl:param name="e" as="element()" />
	<xsl:param name="context" as="element()" />
	<xsl:if test="exists($e/@class)">
		<xsl:variable name="selector" as="xs:string" select="uk:make-class-selector($context, $e)" />
		<xsl:sequence select="uk:get-inline-class-properties-1($context, $selector)" />
	</xsl:if>
</xsl:function>

<!-- style property getter -->

<xsl:function name="uk:get-style-property" as="xs:string?">
	<xsl:param name="e" as="element()" />
	<xsl:param name="prop" as="xs:string" />
	<xsl:if test="exists($e/@style)">
		<xsl:analyze-string select="$e/@style" regex="{ concat($prop, ' *: *([^;]+)') }">
			<xsl:matching-substring>
				<xsl:sequence select="regex-group(1)"/>
			</xsl:matching-substring>
		</xsl:analyze-string>
	</xsl:if>
</xsl:function>

<xsl:function name="uk:get-style-or-class-property" as="xs:string?">
	<xsl:param name="e" as="element()" />
	<xsl:param name="prop" as="xs:string" />
	<xsl:param name="context" as="element()" />
	<xsl:sequence select="uk:get-style-or-class-property($e, $prop, (), $context)" />
</xsl:function>

<xsl:function name="uk:get-style-or-class-property" as="xs:string?">
	<xsl:param name="e" as="element()" />
	<xsl:param name="prop" as="xs:string" />
	<xsl:param name="default" as="xs:string?" />
	<xsl:param name="context" as="element()" />
	<xsl:variable name="from-style-attribute" as="xs:string?" select="uk:get-style-property($e, $prop)" />
	<xsl:variable name="from-class-attribute" as="xs:string?" select="uk:get-class-property($e, $prop, $context)" />
	<xsl:choose>
		<xsl:when test="exists($from-style-attribute)">
			<xsl:sequence select="$from-style-attribute" />
		</xsl:when>
		<xsl:when test="exists($from-class-attribute)">
			<xsl:sequence select="$from-class-attribute" />
		</xsl:when>
		<xsl:otherwise>
			<xsl:sequence select="$default" />
		</xsl:otherwise>
	</xsl:choose>
</xsl:function>

<xsl:function name="uk:extract-alignment" as="xs:string?">
	<xsl:param name="p" as="element()" />
	<xsl:param name="context" as="element()" />
	<xsl:sequence select="uk:get-style-or-class-property($p, 'text-align', $context)" />
</xsl:function>

<xsl:template match="header//p[not(parent::blockContainer)][not(ancestor::authorialNote)] | coverPage/p">
	<xsl:param name="class-context" as="element()" tunnel="yes" />
	<xsl:choose>
		<xsl:when test="exists(child::img) and (every $block in preceding-sibling::* satisfies $block/@name = 'restriction')">
			<div class="judgment-header__logo">
				<xsl:apply-templates>
					<xsl:with-param name="has-underline" select="()" tunnel="yes" />
					<xsl:with-param name="is-uppercase" select="uk:is-uppercase(., $class-context)" tunnel="yes" />
				</xsl:apply-templates>
			</div>
		</xsl:when>
		<xsl:when test="exists(child::neutralCitation)">
			<div class="judgment-header__neutral-citation">
				<xsl:apply-templates>
					<xsl:with-param name="has-underline" select="()" tunnel="yes" />
					<xsl:with-param name="is-uppercase" select="uk:is-uppercase(., $class-context)" tunnel="yes" />
				</xsl:apply-templates>
			</div>
		</xsl:when>
		<xsl:when test="exists(child::docketNumber)">
			<div class="judgment-header__case-number">
				<xsl:apply-templates>
					<xsl:with-param name="has-underline" select="()" tunnel="yes" />
					<xsl:with-param name="is-uppercase" select="uk:is-uppercase(., $class-context)" tunnel="yes" />
				</xsl:apply-templates>
			</div>
		</xsl:when>
		<xsl:when test="exists(child::courtType)">
			<div class="judgment-header__court">
				<xsl:apply-templates>
					<xsl:with-param name="has-underline" select="()" tunnel="yes" />
					<xsl:with-param name="is-uppercase" select="uk:is-uppercase(., $class-context)" tunnel="yes" />
				</xsl:apply-templates>
			</div>
		</xsl:when>
		<xsl:when test="exists(child::docDate)">
			<div class="judgment-header__date">
				<xsl:apply-templates>
					<xsl:with-param name="has-underline" select="()" tunnel="yes" />
					<xsl:with-param name="is-uppercase" select="uk:is-uppercase(., $class-context)" tunnel="yes" />
				</xsl:apply-templates>
			</div>
		</xsl:when>
		<xsl:when test="matches(normalize-space(.), '^- -( -)+$')">
			<div class="judgment-header__line-separator" aria-hidden="true">
				<xsl:apply-templates>
					<xsl:with-param name="has-underline" select="()" tunnel="yes" />
					<xsl:with-param name="is-uppercase" select="uk:is-uppercase(., $class-context)" tunnel="yes" />
				</xsl:apply-templates>
			</div>
		</xsl:when>
		<xsl:otherwise>
			<xsl:variable name="alignment" as="xs:string?" select="uk:extract-alignment(., $class-context)" />
			<xsl:choose>
				<xsl:when test="$alignment = ('center', 'right', 'left')">
					<p>
						<xsl:attribute name="class">
							<xsl:sequence select="concat('judgment-header__pr-', $alignment)" />
						</xsl:attribute>
						<xsl:call-template name="inline" />
					</p>
				</xsl:when>
				<xsl:otherwise>
					<xsl:next-match />
				</xsl:otherwise>
			</xsl:choose>
		</xsl:otherwise>
	</xsl:choose>
</xsl:template>

<!-- alignment of paragraphs in press summary headers -->
<xsl:template match="preface/p" priority="1">
	<xsl:param name="class-context" as="element()" tunnel="yes" />
	<xsl:variable name="alignment" as="xs:string?" select="uk:extract-alignment(., $class-context)" />
	<xsl:choose>
		<xsl:when test="$alignment = ('center', 'right', 'left')">
			<p>
				<xsl:attribute name="class">
					<xsl:sequence select="concat('judgment-header__pr-', $alignment)" />
				</xsl:attribute>
				<xsl:call-template name="inline" />
			</p>
		</xsl:when>
		<xsl:otherwise>
			<xsl:next-match />
		</xsl:otherwise>
	</xsl:choose>
</xsl:template>


<xsl:template match="p">
	<p>
		<xsl:call-template name="inline" />
	</p>
</xsl:template>

<xsl:template match="block">
	<p>
		<xsl:call-template name="inline" />
	</p>
</xsl:template>

<xsl:template match="num | heading">
	<xsl:call-template name="inline" />
</xsl:template>

<xsl:template match="neutralCitation">
	<span class="ncn-nowrap">
		<xsl:call-template name="inline" />
	</span>
</xsl:template>

<xsl:template match="docType | docTitle">
	<xsl:call-template name="inline" />
</xsl:template>

<xsl:template match="courtType | docketNumber | docDate">
	<xsl:call-template name="inline" />
</xsl:template>

<xsl:template match="party | role | judge | lawyer">
	<xsl:call-template name="inline" />
</xsl:template>

<xsl:template match="span">
	<xsl:call-template name="inline" />
</xsl:template>

<!-- all of the inline properties the parser produces -->
<xsl:variable name="inline-properties" as="xs:string+" select="('font-family', 'font-size', 'font-weight', 'font-style', 'font-variant', 'color', 'background-color', 'text-transform', 'text-decoration-line', 'text-decoration-style', 'vertical-align')" />

<xsl:function name="uk:get-combined-inline-styles" as="xs:string*">
	<xsl:param name="e" as="element()" />
	<xsl:param name="context" as="element()" />
	<xsl:variable name="from-class-attr" select="uk:get-inline-class-properties($e, $context)" /><!-- inline formatting implied by the @class -->
	<xsl:variable name="from-style-attr" as="xs:string*"><!-- inline formatting specified in @style -->
		<xsl:for-each select="tokenize($e/@style, ';')">
			<xsl:variable name="prop" as="xs:string" select="normalize-space(substring-before(., ':'))" />
			<xsl:if test="$prop = $inline-properties">
				<xsl:variable name="value" as="xs:string" select="normalize-space(substring-after(., ':'))" />
				<xsl:sequence select="concat($prop, ':', $value)" />
			</xsl:if>
		</xsl:for-each>
	</xsl:variable>
	<xsl:variable name="combined" as="xs:string*"><!-- combined, @style trumps @class -->
		<xsl:variable name="style-properties" as="xs:string*">
			<xsl:for-each select="$from-style-attr">
				<xsl:sequence select="substring-before(., ':')" />
			</xsl:for-each>
		</xsl:variable>
		<xsl:for-each select="$from-class-attr">
			<xsl:variable name="prop" as="xs:string" select="substring-before(., ':')" />
			<xsl:if test="not($prop = $style-properties)">
				<xsl:sequence select="." />
			</xsl:if>
		</xsl:for-each>
		<xsl:sequence select="$from-style-attr" />
	</xsl:variable>
	<!-- remove font, font-size and text-transform -->
	<xsl:for-each select="$combined">
		<xsl:choose>
			<xsl:when test="starts-with(., 'font-family:') and not(contains(., 'Symbol') or contains(., 'Wingdings'))" /> <!-- remove font, except Symbol or Wingdings -->
			<xsl:when test="starts-with(., 'font-size:')" /> <!-- remove font-size -->
			<xsl:when test="starts-with(., 'text-transform:')" /> <!-- remove text-transform -->
			<xsl:when test="starts-with(., 'text-decoration')" /> <!-- remove text-decoration-..., handled by $has-underline -->
			<xsl:otherwise>
				<xsl:sequence select="." />
			</xsl:otherwise>
		</xsl:choose>
	</xsl:for-each>
</xsl:function>

<xsl:template name="inline">
	<xsl:param name="has-underline" as="xs:string*" select="()" tunnel="yes" />
	<xsl:param name="is-uppercase" as="xs:boolean" select="false()" tunnel="yes" />
	<xsl:param name="class-context" as="element()" tunnel="yes" />
	<!-- extract inline styles and recalculate has-underline and is-uppercase -->
	<xsl:variable name="styles" as="xs:string*" select="uk:get-combined-inline-styles(., $class-context)" />
	<xsl:variable name="has-underline" as="xs:string*" select="uk:has-underline(., $has-underline, $class-context)" />
	<xsl:variable name="is-uppercase" as="xs:boolean" select="uk:is-uppercase(., $is-uppercase, $class-context)" />
	<!-- call recursive template -->
	<xsl:call-template name="inline-recursive">
		<xsl:with-param name="styles" select="$styles" />
		<xsl:with-param name="has-underline" select="$has-underline" tunnel="yes" />
		<xsl:with-param name="is-uppercase" select="$is-uppercase" tunnel="yes" />
	</xsl:call-template>
</xsl:template>

<xsl:template name="inline-recursive">
	<xsl:param name="styles" as="xs:string*" />
	<xsl:choose>
		<xsl:when test="exists($styles[starts-with(., 'font-weight:') and not(starts-with(., 'font-weight:normal'))])">
			<b>
				<xsl:if test="exists($styles[starts-with(., 'font-weight:') and not(starts-with(., 'font-weight:bold'))])">
					<xsl:attribute name="style">
						<xsl:value-of select="string-join($styles[starts-with(., 'font-weight:')], ';')" />
					</xsl:attribute>
				</xsl:if>
				<xsl:call-template name="inline-recursive">
					<xsl:with-param name="styles" select="$styles[not(starts-with(., 'font-weight:'))]" />
				</xsl:call-template>
			</b>
		</xsl:when>
		<xsl:when test="exists($styles[starts-with(., 'font-style:') and not(starts-with(., 'font-style:normal'))])">
			<i>
				<xsl:if test="exists($styles[starts-with(., 'font-style:') and not(starts-with(., 'font-style:italic'))])">
					<xsl:attribute name="style">
						<xsl:value-of select="string-join($styles[starts-with(., 'font-style:')], ';')" />
					</xsl:attribute>
				</xsl:if>
				<xsl:call-template name="inline-recursive">
					<xsl:with-param name="styles" select="$styles[not(starts-with(., 'font-style:'))]" />
				</xsl:call-template>
			</i>
		</xsl:when>
		<xsl:when test="exists($styles[. = 'vertical-align:super'])">
			<sup>
				<xsl:call-template name="inline-recursive">
					<xsl:with-param name="styles" select="$styles[not(starts-with(., 'vertical-align:'))]" />
				</xsl:call-template>
			</sup>
		</xsl:when>
		<xsl:when test="exists($styles[. = 'vertical-align:sub'])">
			<sub>
				<xsl:call-template name="inline-recursive">
					<xsl:with-param name="styles" select="$styles[not(starts-with(., 'vertical-align:'))]" />
				</xsl:call-template>
			</sub>
		</xsl:when>
		<xsl:when test="exists($styles)">
			<span>
				<xsl:attribute name="style">
					<xsl:value-of select="string-join($styles, ';')" />
				</xsl:attribute>
				<xsl:apply-templates />
			</span>
		</xsl:when>
		<xsl:otherwise>
			<xsl:apply-templates />
		</xsl:otherwise>
	</xsl:choose>
</xsl:template>

<xsl:template match="img">
	<img>
		<xsl:apply-templates select="@*" />
		<xsl:apply-templates />
	</img>
</xsl:template>
<xsl:template match="img/@src">
	<xsl:attribute name="src">
		<xsl:sequence select="concat($image-prefix, '/', .)" />
	</xsl:attribute>
</xsl:template>

<xsl:template match="img/@style">
	<xsl:next-match>
		<xsl:with-param name="properties" select="('width', 'height')" />
	</xsl:next-match>
</xsl:template>

<xsl:template match="br">
	<br />
</xsl:template>

<xsl:template match="date">
	<xsl:call-template name="inline" />
</xsl:template>


<!-- tables -->

<xsl:template match="table">
	<div class="judgment-body__table">
	<table>
		<xsl:variable name="header-rows" as="element()*" select="*[child::th]" />
		<xsl:if test="exists($header-rows)">
			<thead>
				<xsl:apply-templates select="$header-rows">
					<xsl:with-param name="table-class" as="xs:string?" select="@class" tunnel="yes" />
				</xsl:apply-templates>
			</thead>
		</xsl:if>
		<tbody>
			<xsl:apply-templates select="* except $header-rows">
				<xsl:with-param name="table-class" as="xs:string?" select="@class" tunnel="yes" />
			</xsl:apply-templates>
		</tbody>
	</table>
	</div>
</xsl:template>

<xsl:template match="tr | th | td">
	<xsl:param name="class-context" as="element()" tunnel="yes" />
	<xsl:param name="table-class" as="xs:string?" tunnel="yes" />
	<xsl:element name="{ local-name() }">
		<xsl:copy-of select="@*" />
		<xsl:if test="$table-class">
			<xsl:variable name="selector" as="xs:string" select="concat('.', $table-class, ' ', local-name(.))" /> <!-- e.g., '.TableClass1 td' -->
			<xsl:variable name="selector" as="xs:string" select="uk:augment-simple-class-selector($class-context, $selector)" /> <!-- e.g., '#judgment .TableClass1 td' -->
			<xsl:variable name="table-class-properties" select="uk:get-all-class-properties($class-context, $selector)" />
			<xsl:if test="exists($table-class-properties)">
				<xsl:attribute name="style">
					<xsl:value-of select="string-join($table-class-properties, ';')" />
					<xsl:if test="exists(@style)">
						<xsl:value-of select="';'" />
						<xsl:value-of select="concat(';', @style)" />
					</xsl:if>
				</xsl:attribute>
			</xsl:if>
		</xsl:if>
		<xsl:apply-templates />
	</xsl:element>
</xsl:template>

<!-- header tables -->

<xsl:template match="header//table">
	<xsl:choose>
		<xsl:when test="every $row in * satisfies uk:can-remove-first-column($row)">
			<xsl:apply-templates select="." mode="remove-first-column" />
		</xsl:when>
		<xsl:otherwise>
			<xsl:next-match />
		</xsl:otherwise>
	</xsl:choose>
</xsl:template>

<xsl:function name="uk:can-remove-first-column" as="xs:boolean">
	<xsl:param name="row" as="element()" />
	<xsl:sequence select="count($row/*) = 3 and uk:cell-is-empty($row/*[1])" />
</xsl:function>

<xsl:function name="uk:cell-is-empty" as="xs:boolean">
	<xsl:param name="cell" as="element()" />
	<xsl:sequence select="uk:cell-span-is-effectively-one($cell/@colspan) and uk:cell-span-is-effectively-one($cell/@rowspan) and not(normalize-space(string($cell)))" />
</xsl:function>

<xsl:function name="uk:cell-span-is-effectively-one" as="xs:boolean">
	<xsl:param name="attr" as="attribute()?" />
	<xsl:sequence select="empty($attr) or string($attr) = '' or string($attr) = '1'" />
</xsl:function>

<xsl:template match="table" mode="remove-first-column">
	<table class="pr-two-column">
		<tbody>
			<xsl:apply-templates mode="remove-first-column" />
		</tbody>
	</table>
</xsl:template>

<xsl:template match="tr" mode="remove-first-column">
	<tr>
		<xsl:apply-templates select="*[position() gt 1]" mode="remove-first-column" />
	</tr>
</xsl:template>

<xsl:template match="th | td" mode="remove-first-column">
	<xsl:element name="{ local-name() }">
		<xsl:apply-templates />
	</xsl:element>
</xsl:template>


<!-- links -->

<xsl:template match="a | ref">
	<xsl:choose>
		<xsl:when test="uk:link-is-supported(@href)">
			<a>
				<xsl:apply-templates select="@href" />
				<xsl:call-template name="inline" />
			</a>
		</xsl:when>
		<xsl:otherwise>
			<xsl:call-template name="inline" />
		</xsl:otherwise>
	</xsl:choose>
</xsl:template>


<!-- tables of contents -->

<xsl:template match="toc">
	<div>
		<xsl:apply-templates />
	</div>
</xsl:template>

<xsl:template match="tocItem">
	<p>
		<xsl:call-template name="inline" />
	</p>
</xsl:template>


<!-- markers and attributes -->

<xsl:template match="marker[@name='tab']">
	<span>
		<xsl:text> </xsl:text>
	</span>
</xsl:template>

<xsl:template match="@style">
	<xsl:param name="properties" as="xs:string*" select="('font-weight', 'font-style', 'text-transform', 'font-variant', 'text-decoration-line', 'text-decoration-style')" />
	<xsl:variable name="values" as="xs:string*">
		<xsl:for-each select="tokenize(., ';')">
			<xsl:if test="tokenize(., ':')[1] = $properties">
				<xsl:sequence select="." />
			</xsl:if>
		</xsl:for-each>
	</xsl:variable>
	<xsl:if test="exists($values)">
		<xsl:attribute name="style">
			<xsl:sequence select="string-join($values, ';')" />
		</xsl:attribute>
	</xsl:if>
</xsl:template>

<xsl:template match="@src | @href | @title">
	<xsl:copy />
</xsl:template>

<xsl:template match="@class | @refersTo | @date | @as" />

<xsl:template match="@*" />


<!-- footnotes -->

<xsl:template match="authorialNote">
	<xsl:variable name="marker" as="xs:string" select="@marker" />
	<a id="{ concat('fnref', $marker) }" href="{ concat('#fn', $marker) }" class="judgment-body__footnote-reference">
		<span class="judgment__hidden"> (Footnote: </span>
		<sup>
			<xsl:value-of select="$marker" />
		</sup>
		<span class="judgment__hidden">)</span>
	</a>
</xsl:template>

<xsl:template name="footnotes">
	<xsl:param name="footnotes" as="element()*" select="descendant::authorialNote" />
	<xsl:if test="exists($footnotes)">
		<footer class="judgment-footer">
			<hr />
			<xsl:apply-templates select="$footnotes" mode="footnote" />
		</footer>
	</xsl:if>
</xsl:template>

<xsl:template match="authorialNote" mode="footnote">
	<div>
		<xsl:apply-templates />
	</div>
</xsl:template>

<xsl:template match="authorialNote/p[1]">
	<xsl:variable name="marker" as="xs:string" select="../@marker" />
	<p id="{ concat('fn', $marker) }" class="judgment-footer__footnote">
		<a href="{ concat('#fnref', $marker) }" class="judgment-footer__footnote-backlink">
			<span class="judgment__hidden"> (Footnote reference from: </span>
			<sup>
				<xsl:value-of select="$marker" />
			</sup>
			<span class="judgment__hidden">)</span>
		</a>
		<xsl:text> </xsl:text>
		<xsl:call-template name="inline" />
	</p>
</xsl:template>


<!-- math -->

<xsl:template match="math:*">
	<xsl:element name="{ local-name(.) }">
		<xsl:copy-of select="@*"/>
		<xsl:apply-templates />
	</xsl:element>
</xsl:template>

<!-- search query numbering -->

<xsl:template match="uk:mark">
	<xsl:element name="{ local-name(.) }">
		<xsl:copy-of select="@*"/>
		<xsl:apply-templates />
	</xsl:element>
</xsl:template>

<!-- text -->

<xsl:function name="uk:is-uppercase" as="xs:boolean">
	<xsl:param name="p" as="element()" />
	<xsl:param name="context" as="element()" />
	<xsl:sequence select="uk:is-uppercase($p, false(), $context)" />
</xsl:function>

<xsl:function name="uk:is-uppercase" as="xs:boolean">
	<xsl:param name="e" as="element()" />
	<xsl:param name="default" as="xs:boolean" />
	<xsl:param name="context" as="element()" />
	<xsl:variable name="text-transform" as="xs:string?" select="uk:get-style-or-class-property($e, 'text-transform', $context)" />
	<xsl:choose>
		<xsl:when test="exists($text-transform)">
			<xsl:sequence select="$text-transform = 'uppercase'" />
		</xsl:when>
		<xsl:otherwise>
			<xsl:sequence select="$default" />
		</xsl:otherwise>
	</xsl:choose>
</xsl:function>

<!-- the following two functions return a sequence of 0, 1 or 2 values:
	the first is for the text-decoration-line property,
	the second is for the text-decoration-style property -->

<xsl:function name="uk:has-underline" as="xs:string*">
	<xsl:param name="p" as="element()" />
	<xsl:param name="context" as="element()" />
	<xsl:sequence select="uk:has-underline($p, (), $context)" />
</xsl:function>

<xsl:function name="uk:has-underline" as="xs:string*">
	<xsl:param name="e" as="element()" />
	<xsl:param name="default" as="xs:string*" />
	<xsl:param name="context" as="element()" />
	<xsl:variable name="decor-line" as="xs:string?" select="uk:get-style-or-class-property($e, 'text-decoration-line', $default[1], $context)" />
	<xsl:variable name="decor-style" as="xs:string?" select="uk:get-style-or-class-property($e, 'text-decoration-style', $default[2], $context)" />
	<xsl:sequence select="$decor-line" />
	<xsl:if test="exists($decor-line)">
		<xsl:sequence select="$decor-style" />
	</xsl:if>
</xsl:function>

<xsl:template match="text()">
	<xsl:param name="has-underline" as="xs:string*" select="()" tunnel="yes" />
	<xsl:param name="is-uppercase" as="xs:boolean" select="false()" tunnel="yes" />
	<xsl:choose>
		<xsl:when test="exists($has-underline) and $has-underline[1] = 'none'">
			<xsl:next-match>
				<xsl:with-param name="has-underline" select="()" tunnel="yes" />
			</xsl:next-match>
		</xsl:when>
		<xsl:when test="exists($has-underline)">
			<xsl:variable name="decor-line" as="xs:string" select="$has-underline[1]" />
			<xsl:variable name="decor-style" as="xs:string?" select="$has-underline[2]" />
			<xsl:variable name="styles" as="xs:string*">
				<xsl:if test="$decor-line != 'underline'">
					<xsl:sequence select="concat('text-decoration-line:', $decor-line)" />
				</xsl:if>
				<xsl:if test="exists($decor-style) and $decor-style != 'solid'">
					<xsl:sequence select="concat('text-decoration-style:', $decor-style)" />
				</xsl:if>
			</xsl:variable>
			<u>
				<xsl:if test="exists($styles)">
					<xsl:attribute name="style">
						<xsl:sequence select="string-join($styles, ';')" />
					</xsl:attribute>
				</xsl:if>
				<xsl:next-match>
					<xsl:with-param name="has-underline" select="()" tunnel="yes" />
				</xsl:next-match>
			</u>
		</xsl:when>
		<xsl:when test="$is-uppercase">
			<xsl:value-of select="upper-case(.)" />
		</xsl:when>
		<xsl:otherwise>
			<xsl:copy />
		</xsl:otherwise>
	</xsl:choose>
</xsl:template>

</xsl:transform>
